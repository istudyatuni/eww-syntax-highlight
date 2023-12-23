### Generate `widgets.json`

Apply patch [`gen-docs-patch.diff`](gen-docs-patch.diff) and build:

```sh
# from root folder if this repo
cp docs/gen-docs-patch.diff path/to/eww/repo/patch.diff
cd path/to/eww/repo
git apply patch.diff
deno run --allow-read --allow-write gen-docs.ts ./crates/eww/src/widgets/widget_definitions.rs ./crates/eww/src/config/inbuilt.rs
cd -
mv path/to/eww/repo/widgets.json .
```
