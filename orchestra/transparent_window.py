import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk
import cairo

class TransparentOverlay(Gtk.Window):
    def __init__(self, image_path):
        super().__init__(title="Overlay")
        self.set_decorated(False)
        self.set_keep_above(True)
        self.set_app_paintable(True)

        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual:
            self.set_visual(visual)

        # Use CSS for opacity instead of deprecated set_opacity
        css = Gtk.CssProvider()
        css.load_from_data(b"window { opacity: 0.5; }")
        Gtk.StyleContext.add_provider_for_screen(
            screen, css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        image = Gtk.Image.new_from_file(image_path)
        self.add(image)

        # Make window click-through
        self.realize()
        surface = self.get_window().create_similar_surface(
            cairo.Content.COLOR_ALPHA, 1, 1
        )
        region = Gdk.cairo_region_create_from_surface(surface)
        self.get_window().input_shape_combine_region(region, 0, 0)

        self.show_all()

overlay = TransparentOverlay("/home/harish/Downloads/CatacombsMarkedAreas.jpg")
Gtk.main()