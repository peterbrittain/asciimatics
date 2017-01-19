.. _animation-ref:

Animation
=========

Scenes and Effects
------------------
The asciimatics package gets its name from a storyboard technique in films
('animatics') where simple animations and mock-ups are used to get a better
feel for the planned film.  Much like these storyboards, you need two key
elements for your animation.

1. One or more :py:obj:`.Scene` objects that encompass the key stages of your
   animation.
2. One or more :py:obj:`.Effect` objects in each Scene that actually display
   something on the Screen.

An Effect is basically an object that encodes something to be displayed on the
Screen.  It can be anything from :py:obj:`.Print` that just displays some
rendered text at a specific location for a certain time to :py:obj:`.Snow` that
adds dynamically generated falling snow to the Scene.  These are the building
blocks of your animation and will be rendered in the strict order that they
appear in the Scene, so most of the time you want to put foreground Effects
last to ensure they overwrite anything else.

There is no hard and fast rule of how to divide up your Scenes, though there is
normally a natural cut where you want to move between effects or clear the
Screen, much like you'd need to move to a different cell in a comic strip.
These cuts are where you should consider creating a new Scene.

Once you have built up a set of Effects into a list of one or more Scenes, you
can pass this list to :py:meth:`.play` which will run through the Scenes in
order, or stop playing if the user exits by pressing 'q' (assuming you use the
default key handling).

If you cannot allow asciimatics to schedule each frame itself, e.g. because you
are using an asynchronous framework of your own like gevent or twisted, you
can use :py:meth:`.set_scenes` to set up your scenes and
:py:meth:`.draw_next_frame` (every 1/20 of a second) to draw the next frame.

Sprites and Paths
-----------------
A :py:obj:`.Sprite` is a special Effect designed to move some rendered text
around the Screen, thus creating an animated character.  As such, they work
like any other Effect, needing to be placed in a Scene and passed to the Screen
(through the ``play()`` method) to be displayed.  They typically take:

- a set of Renderers to animate the motion of the character when moving in any
  direction
- a default Renderer (to be used when standing still)
- a path to define where the Sprite moves.

Much like Renderers, the paths come in 2 flavours:

1. A :py:obj:`.Path` is a pre-defined path that can be fully determined at the
   start of the program.  This provides 4 methods - ``jump_to()``, ``wait()``,
   ``move_straight_to()`` and ``move_round_to()`` - to define the path.  Just
   decide on the path and script it by chaining these methods together.
2. A :py:obj:`.DynamicPath` which depends on the program state and so can only
   be calculated when needed - e.g. because it depends on what key the user is
   pressing.  These provide an abstract method - ``process_event()`` - that
   must be overridden to handle any keys and Update the current coordinates
   of the Path, to be returned the next time the Sprite asks for an update.

The full declaration of a Sprite is therefore something like this.

.. code-block:: python

    # Sample Sprite that plots an "X" for each step along an elliptical path.
    centre = (screen.width // 2, screen.height // 2)
    curve_path = []
    for i in range(0, 11):
        curve_path.append(
            (centre[0] + (screen.width / 4 * math.sin(i * math.pi / 5)),
             centre[1] - (screen.height / 4 * math.cos(i * math.pi / 5))))
    path = Path()
    path.jump_to(centre[0], centre[1] - screen.height // 4),
    path.move_round_to(curve_path, 60)
    sprite = Sprite(
        screen,
        renderer_dict={
            "default": StaticRenderer(images=["X"])
        },
        path=path,
        colour=Screen.COLOUR_RED,
        clear=False)

For more examples of using Sprites, including dynamic Paths, see the samples
directory.

Particle Systems
----------------
A :py:obj:`.ParticleEffect` is a special Effect designed to draw a `particle
system <https://en.m.wikipedia.org/wiki/Particle_system>`_.  It consists of one
or more :py:obj:`.ParticleEmitter` objects which in turn contains one or
more :py:obj:`.Particle` objects.

The ``ParticleEffect`` defines a chain of ``ParticleEmitter``\ s that
spawn one or more ``Particle``\ s, each with a unique set of attributes - e.g.
location, direction, colour, etc.  The ``ParticleEffect`` renders a frame by
rendering each of these ``Particle``\ s and then updating them following the
rules defined by the ``ParticleEmitter``.

It all sounds a bit convoluted, doesn't it?  Let's try a concrete example to
clarify it...  Consider the :py:obj:`.StarFirework` effect.  This is constructed
as follows.

1. The ``StarFirework`` constructs a ``Rocket``.  This is a ``ParticleEmitter``
   that has just one ``Particle`` that shoots vertically up the Screen to hit a
   pre-defined end point.
2. When this ``Particle`` hits its end-point, it expires and spawns a
   ``StarExplosion``.  This is a ``ParticleEmitter`` that spawns many
   ``Particle``\ s in such a way that they are explode outwards radially from
   where the ``Rocket`` expired.
3. In turn, each of these ``Particle``\ s from the ``StarExplosion`` spawns a
   ``StarTrail`` on each new frame.  These are ``ParticleSystem``\ s that spawn
   a single ``Particle`` which just hovers for a few frames and fades away.

Putting this all together (by playing the Effect) you have a classic exploding
firework.  For more examples, see the other Effects in the particles and
fireworks samples.

CPU Considerations
------------------
Many people run asciimatics on low-power systems and so care about CPU.  However
there is a trade-off between CPU usage and responsiveness of any User Interface
or the slickness of any animation.  Asciimatics tries to handle this for you by
looking at when each ``Effect`` next wants to be redrawn and only refreshing the
``Screen`` when needed.

For most use-cases, this default should be enough for your needs.  However,
there are a couple of cases where you might need more.  The first is very
low-power (e.g. SOC) systems where you need to keep CPU usage to a minimum for
a widget-based UI.  In this case, you can use the ``reduce_cpu`` parameter
when constructing your :py:obj:`.Frame`.

The other case, is actually the opposite problem - you may find that
asciimatics is being too conservative and you need to refresh the ``Screen``
before it thinks you need to do so.  In this case, you can simply force its hand
by calling :py:meth:`.force_update`, which will force a full refresh of the
``Screen`` next time that :py:meth:`.draw_next_frame` is called.