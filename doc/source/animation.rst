Animation
---------
The asciimatics package gets its name from a storyboard technique in films ('animatics') where simple animations and mock-ups are used to get a better feel for the planned film.  Much like these storyboards, you need two key elements for your animation.

1. One or more  :py:obj:`.Scene` objects that encompass the key stages of you animation.  There is no hard and fast rule of how to divide up your Scenes, though there is normally a natural cut where you want to move between effects or clear the Screen, much like you'd need to move to a different cell in a comic strip.  These cuts are where you should consider creating a new Scene.

2. One or more :py:obj:`.Effect` objects in each Scene.  An Effect is basically an object that encodes something to be displayed on the Screen.  It can be anything from :py:obj:`.Print` that just displays some rendered text at a specific location for a certain time to :py:obj:`.Snow` that adds dynamically generated falling snow to the Scene.  These are the building blocks of your animation and will be rendered in the strict order that they appear in the Scene, so most of the time you want to put foreground Effects last to ensure they overwrite anything else.

Once you have built up a set of Effects into a list of one or more Scenes, you can pass this list to :py:meth:`.play` which will run through the Scenes in order, or stop playing if the user exits by pressing 'q'.
