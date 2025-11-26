# treesitter

to setup tree sitter:

git clone --depth=1 https://github.com/tree-sitter/tree-sitter-python .cache/tree-sitter-python
git clone --depth=1 https://github.com/tree-sitter/tree-sitter-javascript .cache/tree-sitter-javacript

tree-sitter build-lib -o .cache/treesitter-langs
