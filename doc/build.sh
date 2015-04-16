PYTHONPATH=.. sphinx-apidoc ../asciimatics -o ./source -f
cat source/asciimatics.rst | grep -v "undoc" > source/tmp.rst
mv -f source/tmp.rst source/asciimatics.rst
PYTHONPATH=.. sphinx-build -b html ./source ./build
