PYTHONPATH=.. sphinx-apidoc ../asciimatics -o ./source -f
cat source/asciimatics.rst | awk -- '/:undoc-members:/ {next} { print $0 } /:members:/ { print "   :inherited-members:"}' > source/tmp.rst
mv -f source/tmp.rst source/asciimatics.rst
cat source/asciimatics.widgets.rst | awk -- '/:undoc-members:/ {next} { print $0 } /:members:/ { print "   :inherited-members:"}' > source/tmp.rst
mv -f source/tmp.rst source/asciimatics.widgets.rst
cat source/asciimatics.renderers.rst | awk -- '/:undoc-members:/ {next} { print $0 } /:members:/ { print "   :inherited-members:"}' > source/tmp.rst
mv -f source/tmp.rst source/asciimatics.renderers.rst
PYTHONPATH=.. sphinx-build -b html ./source ./build
