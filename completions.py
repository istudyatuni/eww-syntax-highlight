from collections import namedtuple
from itertools import chain
from typing import List
import json

import sublime
import sublime_plugin

PKG_NAME = 'eww-syntax-highlight'

Completion = namedtuple('Completion', ['trigger', 'data', 'kind', 'annotation', 'details'])

# idea of removing optional parameters in some snippets when value is deleted
# (scary regex) is modified version from
# https://github.com/rust-lang/rust-enhanced/blob/master/snippets/fn.sublime-snippet
available_keyword = [
    {"trigger": "definclude", "file": "include.yuck", "annotation": "(include ..)"},
    {"trigger": "defwindow-x11", "file": "window-x11.yuck", "annotation": "(defwindow ..)"},
    {"trigger": "defwindow-wayland", "file": "window-wayland.yuck", "annotation": "(defwindow ..)"},
    {"trigger": "defvar", "file": "var.yuck", "annotation": "(defvar .. \"..\")"},
    {"trigger": "defpoll", "file": "poll.yuck", "annotation": "(defpoll .. :interval .. `..`)"},
    {"trigger": "deflisten", "file": "listen.yuck", "annotation": "(deflisten .. `..`)"},
    {"trigger": "defwidget", "file": "widget.yuck", "annotation": "(defwidget .. [])"},
]

kinds = {
    'function': sublime.KIND_FUNCTION,
    'keyword': sublime.KIND_KEYWORD,
    'variable': sublime.KIND_VARIABLE,
}

class EwwCompletions(sublime_plugin.EventListener):
    # probably this should be configured via settings
    attr_format = ':{widget_name}|{attr_name}'
    attr_annot_format = '{attr_type}'
    # attr_annot_format = '{attr_type}, for {widget_name}'
    # attr_annot_format = 'for {widget_name}, {attr_type}'

    def on_query_completions(self, view: sublime.View, prefix: str, locations: List[int]) -> sublime.CompletionList:
        if not view.match_selector(locations[0], "source.yuck"):
            return sublime.CompletionList([])

        available_keyword_completions = []
        for a in available_keyword:
            available_keyword_completions.append(Completion(
                a['trigger'],
                EwwCompletions.read_completion(a['file']),
                'keyword',
                a['annotation'],
                '',
            ))

        out = []
        for comp in chain(available_keyword_completions, EwwCompletions.read_parse_widgets()):
            out.append(sublime.CompletionItem(
                comp.trigger,
                comp.annotation,
                comp.data,
                sublime.COMPLETION_FORMAT_SNIPPET,
                kinds[comp.kind],
                comp.details,
            ))

        return sublime.CompletionList(out)

    @staticmethod
    def read_completion(path: str):
        with open(f'{sublime.packages_path()}/{PKG_NAME}/completions/{path}') as f:
            return f.read().strip()

    @staticmethod
    def read_parse_widgets():
        # this file generated with slightly tweaked
        # https://github.com/elkowar/eww/blob/master/gen-docs.ts
        with open(f'{sublime.packages_path()}/{PKG_NAME}/widgets.json') as f:
            content = json.load(f)

        res: List[Completion] = []
        # separate array for showing props completions after widgets completions
        props = []
        for w in content:
            widget_name = w['name']
            if widget_name == 'a checkbox':
                # just fix strange name
                widget_name = 'checkbox'

            if widget_name == 'widget':
                # props available for all widgets
                widget_name = 'all'
            else:
                widget_desc = w['desc']
                res.append(Completion(
                    widget_name,
                    "(" + widget_name + " $1)",
                    'function',
                    "(" + widget_name + " ..)",
                    widget_desc,
                ))

            for p in w['props']:
                param_type = p['type']
                param_name: str = p['name']
                param_desc = p['desc']
                if param_name.startswith('on'):
                    # this is a shell command
                    param_data = ':' + param_name + ' `$1`'
                elif param_type in ('string', 'duration'):
                    param_data = ':' + param_name + ' "$1"'
                elif param_type == 'vec':
                    param_data = ':' + param_name + ' ($1)'
                else:
                    param_data = ':' + param_name + ' $1'

                if widget_name == 'all':
                    trigger = f':{param_name}'
                else:
                    trigger = EwwCompletions.attr_format.format(widget_name=widget_name, attr_name=param_name)

                props.append(Completion(
                    trigger,
                    param_data,
                    'variable',
                    EwwCompletions.attr_annot_format.format(attr_type=param_type, widget_name=widget_name),
                    param_desc,
                ))

        return chain(res, props)
