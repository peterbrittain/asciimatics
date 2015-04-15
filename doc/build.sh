PYTHONPATH=.. sphinx-apidoc ../asciimatics -o ./source -f
PYTHONPATH=.. sphinx-build -b html ./source ./build
