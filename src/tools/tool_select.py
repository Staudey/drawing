# tool_select.py

from gi.repository import Gtk, Gdk, GdkPixbuf
import cairo

from .abstract_tool import ToolTemplate
from .utilities import utilities_get_magic_path

class ToolSelect(ToolTemplate):
	__gtype_name__ = 'ToolSelect'

	closing_precision = 10

	def __init__(self, window, **kwargs):
		super().__init__('select', _("Selection"), 'tool-select-symbolic', window)
		self.use_color = False
		self.selected_type_id = 'rectangle'
		self.selected_type_label = _("Rectangle selection")
		self.background_type_id = 'transparent'
		self.temp_path = None
		self.temp_x = 0
		self.temp_y = 0
		self.closing_x = 0
		self.closing_y = 0

		self.add_tool_action_simple('selection_unselect', self.action_unselect)
		self.add_tool_action_simple('selection_cut', self.action_cut)
		self.add_tool_action_simple('selection_copy', self.action_copy)
		self.add_tool_action_simple('selection_delete', self.action_selection_delete)

		self.add_tool_action_simple('selection_crop', self.action_selection_crop)
		self.add_tool_action_simple('selection_scale', self.action_selection_scale)
		self.add_tool_action_simple('selection_flip', self.action_selection_flip)
		self.add_tool_action_simple('selection_rotate', self.action_selection_rotate)
		self.add_tool_action_simple('selection_saturate', self.action_selection_saturate)

		builder = Gtk.Builder.new_from_resource('/com/github/maoschanz/drawing/tools/ui/tool_select.ui')

		menu_r = builder.get_object('right-click-menu')
		self.rightc_popover = Gtk.Popover.new_from_model(self.window.notebook, menu_r)
		menu_l = builder.get_object('left-click-menu')
		self.selection_popover = Gtk.Popover.new_from_model(self.window.notebook, menu_l)

		self.add_tool_action_enum('selection_type', self.selected_type_id)

		self.exclude_color = False
		# self.add_tool_action_boolean('selection_exclude', self.exclude_color)

		self.selection_has_been_used = False
		self.selection_is_active = False
		self.reset_temp()

	def on_tool_selected(self):
		self.selection_has_been_used = True
		self.update_actions_state()
		self.selection_popover.set_relative_to(self.get_image())
		self.update_surface()

	def on_tool_unselected(self):
		self.set_actions_state(False)

	def update_actions_state(self):
		if self.selection_is_active:
			self.cursor_name = 'grab'
		else:
			self.cursor_name = 'cell'
		self.set_actions_state(self.selection_is_active)

	def set_actions_state(self, state):
		self.set_action_sensitivity('selection_unselect', state)
		self.set_action_sensitivity('selection_cut', state)
		self.set_action_sensitivity('selection_copy', state)
		self.set_action_sensitivity('selection_delete', state)
		self.set_action_sensitivity('selection_export', state)

	def set_active_type(self, *args):
		selection_type = self.get_option_value('selection_type')
		if selection_type == 'rectangle':
			self.selected_type_id = 'rectangle'
			self.selected_type_label = _("Rectangle selection")
		elif selection_type == 'freehand':
			self.selected_type_id = 'freehand'
			self.selected_type_label = _("Free selection")
		else:
			self.selected_type_id = 'color'
			self.selected_type_label = _("Color selection")

	def get_options_label(self):
		return _("Selection options")
		# return self.selected_type_label # XXX better ?

	def get_edition_status(self):
		self.set_active_type()
		# self.exclude_color = self.get_option_value('selection_exclude')
		label = self.selected_type_label
		if self.selection_is_active:
			label = label + ' - ' +  _("Drag the selection or right-click on the canvas")
		else:
			label = label + ' - ' +  _("Select an area or right-click on the canvas")
		return label

	############################################################################

	def give_back_control(self):
		if self.selection_has_been_used:
			if self.selection_is_active:
				operation = self.build_operation()
				self.apply_operation(operation)
			self.forget_selection()
			self.reset_temp()
			return False
		else:
			self.selection_has_been_used = True # XXX ???
			self.forget_selection()
			return self.cancel_ongoing_operation()

	def cancel_ongoing_operation(self):
		self.reset_temp()
		self.restore_pixbuf()
		self.non_destructive_show_modif()
		self.selection_has_been_used = False
		return True

	def on_press_on_area(self, area, event, surface, tool_width, left_color, right_color, event_x, event_y):
		# self.secondary_color = right_color
		self.x_press = event_x
		self.y_press = event_y
		if self.selection_is_active and self.press_point_is_in_selection():
			self.cursor_name = 'grabbing'
			self.window.set_cursor(True)
		if self.selected_type_id == 'color' and not self.selection_is_active:
			self.get_image().selection_path = utilities_get_magic_path(surface, \
				event_x, event_y, self.window, 1)
		elif self.selected_type_id == 'freehand' and not self.selection_is_active:
			self.init_path(event_x, event_y)
		if not self.press_point_is_in_selection():
			self.cursor_name = 'cell'
			self.window.set_cursor(True)
			self.give_back_control()
			self.restore_pixbuf()
			self.non_destructive_show_modif()
		if self.selected_type_id == 'rectangle' and not self.selection_is_active:
			self.init_path(event_x, event_y)

	def on_motion_on_area(self, area, event, surface, event_x, event_y):
		if self.selection_is_active:
			pass
			# self.update_surface() # XXX inutile pour le moment car on n'update pas
			# du tout selection_x et selection_y TODO
		else:
			if self.selected_type_id == 'freehand':
				self.restore_pixbuf()
				self.draw_polygon(event_x, event_y)

	def on_actions_btn_clicked(self, *args):
		self.set_rightc_popover_position( self.get_image().get_allocated_width()/2, \
			self.get_image().get_allocated_height()/2 )
		self.show_popover(True)

	def set_rightc_popover_position(self, x, y):
		rectangle = Gdk.Rectangle()
		rectangle.x = int(x)
		rectangle.y = int(y)
		rectangle.height = 1
		rectangle.width = 1
		self.rightc_popover.set_pointing_to(rectangle)
		self.rightc_popover.set_relative_to(self.get_image())

	def on_release_on_area(self, area, event, surface, event_x, event_y):
		if event.button == 3:
			self.set_rightc_popover_position(event.x, event.y)
			self.show_popover(True)
			return
		elif not self.selection_is_active:
			if self.selected_type_id == 'rectangle':
				self.draw_rectangle(event_x, event_y)
				if self.selection_is_active:
					self.show_popover(True)
					self.selection_has_been_used = False
			elif self.selected_type_id == 'freehand':
				if self.draw_polygon(event_x, event_y):
					self.restore_pixbuf()
					self.create_free_selection_from_main()
					if self.selection_is_active:
						self.show_popover(True)
						self.selection_has_been_used = False
				else:
					return # without updating the surface so the path is visible
			elif self.selected_type_id == 'color':
				self.restore_pixbuf()
				if self.get_image().selection_path is not None:
					self.create_free_selection_from_main()
					if self.selection_is_active:
						self.show_popover(True)
						self.selection_has_been_used = False
			self.update_surface()
		elif self.press_point_is_in_selection():
			self.drag_to(event_x, event_y)
			self.cursor_name = 'grab'
			self.window.set_cursor(True)
			self.update_surface()
		else:
			self.restore_pixbuf()
			self.non_destructive_show_modif()

	def update_surface(self):
		operation = self.build_operation()
		self.do_tool_operation(operation)
		self.non_destructive_show_modif()

	def show_popover(self, state):
		self.selection_popover.popdown()
		self.rightc_popover.popdown()
		if self.selection_is_active and state:
			self.set_popover_position()
			self.selection_popover.popup()
		elif state:
			self.temp_x = self.rightc_popover.get_pointing_to()[1].x
			self.temp_y = self.rightc_popover.get_pointing_to()[1].y
			self.get_image().selection_x = self.rightc_popover.get_pointing_to()[1].x
			self.get_image().selection_y = self.rightc_popover.get_pointing_to()[1].y
			self.rightc_popover.popup()

	def set_popover_position(self):
		rectangle = Gdk.Rectangle()
		main_x, main_y = self.get_image().get_main_coord()
		x = self.get_image().selection_x + self.get_selection_pixbuf().get_width()/2 - main_x
		y = self.get_image().selection_y + self.get_selection_pixbuf().get_height()/2 - main_y
		x = max(0, min(x, self.get_image().get_allocated_width()))
		y = max(0, min(y, self.get_image().get_allocated_height()))
		[rectangle.x, rectangle.y] = [x, y]
		rectangle.height = 1
		rectangle.width = 1
		self.selection_popover.set_pointing_to(rectangle)

	def drag_to(self, final_x, final_y):
		delta_x = final_x - self.x_press
		delta_y = final_y - self.y_press
		self.restore_pixbuf()
		if delta_x == 0 and delta_y == 0:
			pass
		else:
			self.selection_has_been_used = True
			self.get_image().selection_x += delta_x
			self.get_image().selection_y += delta_y
		self.non_destructive_show_modif()

	def action_cut(self, *args):
		self.copy_operation()
		self.action_selection_delete()

	def action_copy(self, *args):
		self.selection_has_been_used = True
		self.copy_operation()

	def copy_operation(self):
		cb = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
		cb.set_image(self.get_selection_pixbuf())

	def selection_import(self):
		self.temp_path = None
		self.create_selection_from_arbitrary_pixbuf(False)

	def selection_paste(self):
		self.temp_path = None
		self.create_selection_from_arbitrary_pixbuf(False)

	def selection_select_all(self):
		self.selection_has_been_used = False
		self.temp_x = 0
		self.temp_y = 0
		self.create_selection_from_arbitrary_pixbuf(True)
		self.show_popover(True)

	def action_unselect(self, *args):
		self.give_back_control()
		self.non_destructive_show_modif() # utile ??

	def action_selection_delete(self, *args):
		self.selection_has_been_used = True
		self.restore_pixbuf()
		self.delete_temp()
		self.reset_temp()
		self.apply_to_pixbuf() # actually needed

	def action_selection_flip(self, *args):
		self.try_edit('flip')

	def action_selection_scale(self, *args):
		self.try_edit('scale')

	def action_selection_crop(self, *args):
		self.try_edit('crop')

	def action_selection_saturate(self, *args):
		self.try_edit('saturate')

	def action_selection_rotate(self, *args):
		self.try_edit('rotate')

	def try_edit(self, tool_id):
		if self.selection_is_active:
			self.window.hijack_begin(self.id, tool_id)
		else:
			self.window.tools[tool_id].row.set_active(True)

	###################### XXX pour toute cette section, ne peut-on pas donner le contexte en paramètre ?

	def init_path(self, event_x, event_y):
		"""This method moves the current path to the "press" event coordinates.
		It's used by both the "rectangle selection" mode and the "free
		selection" mode."""
		if self.get_image().selection_path is not None:
			return
		self.closing_x = event_x
		self.closing_y = event_y
		cairo_context = cairo.Context(self.get_surface())
		cairo_context.move_to(event_x, event_y)
		self.get_image().selection_path = cairo_context.copy_path()

	def draw_polygon(self, event_x, event_y):
		"""This method is specific to the "free selection" mode."""
		cairo_context = cairo.Context(self.get_surface())
		cairo_context.set_source_rgba(0.5, 0.5, 0.5, 0.5)
		cairo_context.set_dash([3, 3])
		if self.get_image().selection_path is None:
			return False
		if (max(event_x, self.closing_x) - min(event_x, self.closing_x) < self.closing_precision) \
		and (max(event_y, self.closing_y) - min(event_y, self.closing_y) < self.closing_precision):
			cairo_context.append_path(self.get_image().selection_path)
			cairo_context.close_path()
			cairo_context.stroke_preserve()
			self.get_image().selection_path = cairo_context.copy_path()
			self.temp_path = cairo_context.copy_path()
			return True
		else:
			cairo_context.append_path(self.get_image().selection_path)
			self.continue_polygon(cairo_context, event_x, event_y)
			return False

	def continue_polygon(self, cairo_context, x, y):
		"""This method is specific to the "free selection" mode."""
		cairo_context.line_to(int(x), int(y))
		cairo_context.stroke_preserve() # draw the line without closing the path
		self.get_image().selection_path = cairo_context.copy_path()
		self.non_destructive_show_modif()

	def draw_rectangle(self, event_x, event_y):
		"""Define the selection pixbuf and draw an overlay for a rectangle
		selection beginning where the "press" event was made and ending where
		the "release" event is made (its coordinates are parameters). This
		method is specific to the "rectangle selection" mode."""
		cairo_context = cairo.Context(self.get_surface())
		cairo_context.set_source_rgba(0.5, 0.5, 0.5, 0.5)
		cairo_context.set_dash([3, 3])
		cairo_context.append_path(self.get_image().selection_path)
		press_x, press_y = cairo_context.get_current_point()

		x0 = int( min(press_x, event_x) )
		y0 = int( min(press_y, event_y) )
		x1 = int( max(press_x, event_x) )
		y1 = int( max(press_y, event_y) )
		w = x1 - x0
		h = y1 - y0
		if w <= 0 or h <= 0:
			self.get_image().selection_path = None
			return

		self.get_image().selection_x = x0
		self.get_image().selection_y = y0
		temp_surface = Gdk.cairo_surface_create_from_pixbuf(self.get_main_pixbuf(), 0, None)
		temp_surface = temp_surface.map_to_image(cairo.RectangleInt(x0, y0, w, h))
		self.get_image().set_selection_pixbuf( Gdk.pixbuf_get_from_surface(temp_surface, \
			0, 0, temp_surface.get_width(), temp_surface.get_height()) )

		cairo_context.new_path()
		cairo_context.move_to(x0, y0)
		cairo_context.line_to(x1, y0)
		cairo_context.line_to(x1, y1)
		cairo_context.line_to(x0, y1)
		cairo_context.close_path()

		self.get_image().selection_path = cairo_context.copy_path()
		self.temp_path = cairo_context.copy_path()
		self.set_temp()

	############################################################################

	def create_selection_from_arbitrary_pixbuf(self, is_existing_content):
		"""This method creates a selection from a pixbuf whose shape is unknown.
		It can be the result of an editing operation (crop, scale, etc.), or it
		can be an imported picture (from a file or from the clipboard).
		In the first case, the "is_existing_content" boolean parameter should be
		true, so the temp_path will be cleared."""
		self.temp_x = self.get_image().selection_x
		self.temp_y = self.get_image().selection_y
		self.selection_has_been_used = True
		self.selection_is_active = True
		cairo_context = cairo.Context(self.get_surface())
		cairo_context.move_to(self.get_image().selection_x, self.get_image().selection_y)
		cairo_context.rel_line_to(self.get_selection_pixbuf().get_width(), 0)
		cairo_context.rel_line_to(0, self.get_selection_pixbuf().get_height())
		cairo_context.rel_line_to(-1 * self.get_selection_pixbuf().get_width(), 0)
		cairo_context.close_path()
		self.get_image().selection_path = cairo_context.copy_path()
		if is_existing_content:
			self.temp_path = cairo_context.copy_path()
			self.set_temp()
		self.show_popover(False)
		self.update_actions_state()
		self.update_surface()

	def reset_temp(self):
		self.temp_x = 0
		self.temp_y = 0
		self.temp_path = None
		self.selection_is_active = False
		self.update_actions_state()

	def set_temp(self):
		self.temp_x = self.get_image().selection_x
		self.temp_y = self.get_image().selection_y
		self.selection_is_active = True
		self.update_actions_state()

		if self.exclude_color:
			self.get_image().selection_pixbuf = \
				self.get_image().selection_pixbuf.add_alpha(True, \
				int(255 * self.secondary_color.red), \
				int(255 * self.secondary_color.green), \
				int(255 * self.secondary_color.blue))

	def delete_temp(self):
		if self.temp_path is None or not self.selection_is_active:
			return
		cairo_context = cairo.Context(self.get_surface())
		cairo_context.new_path()
		cairo_context.append_path(self.temp_path)
		cairo_context.clip()
		cairo_context.set_operator(cairo.Operator.CLEAR)
		cairo_context.paint()
		cairo_context.set_operator(cairo.Operator.OVER)

	def press_point_is_in_selection(self):
		"""Returns a boolean if the point whose coordinates are "(self.x_press,
		self.y_press)" is in the path defining the selection. If such path
		doesn't exist, it returns None."""
		if not self.selection_is_active:
			return True
		if self.get_image().selection_path is None:
			return None
		cairo_context = cairo.Context(self.get_surface())
		for pts in self.get_image().selection_path:
			if pts[1] is not ():
				x = pts[1][0] + self.get_image().selection_x - self.temp_x
				y = pts[1][1] + self.get_image().selection_y - self.temp_y
				cairo_context.line_to(int(x), int(y))
		return cairo_context.in_fill(self.x_press, self.y_press)

	def on_confirm_hijacked_modif(self):
		self.selection_has_been_used = True
		self.window.hijack_end()
		self.create_selection_from_arbitrary_pixbuf(False)

	def create_free_selection_from_main(self):
		self.get_image().selection_pixbuf = self.get_main_pixbuf().copy()
		surface = Gdk.cairo_surface_create_from_pixbuf(self.get_selection_pixbuf(), 0, None)
		xmin, ymin = surface.get_width(), surface.get_height()
		xmax, ymax = 0.0, 0.0
		if self.get_image().selection_path is None:
			return
		for pts in self.get_image().selection_path: # XXX cairo has a method for this
			if pts[1] is not ():
				xmin = min(pts[1][0], xmin)
				xmax = max(pts[1][0], xmax)
				ymin = min(pts[1][1], ymin)
				ymax = max(pts[1][1], ymax)
		xmax = min(xmax, surface.get_width())
		ymax = min(ymax, surface.get_height())
		xmin = max(xmin, 0.0)
		ymin = max(ymin, 0.0)
		if xmax - xmin < self.closing_precision and ymax - ymin < self.closing_precision:
			return # when the path is not drawable yet XXX
		self.crop_free_selection_pixbuf(xmin, ymin, xmax - xmin, ymax - ymin)
		cairo_context = cairo.Context(surface)
		cairo_context.set_operator(cairo.Operator.DEST_IN)
		cairo_context.new_path()
		cairo_context.append_path(self.get_image().selection_path)
		if self.temp_path is None: # ??
			self.temp_path = cairo_context.copy_path()
		cairo_context.fill()
		cairo_context.set_operator(cairo.Operator.OVER)
		self.get_image().selection_pixbuf = Gdk.pixbuf_get_from_surface(surface, xmin, ymin, \
			xmax - xmin, ymax - ymin)
		self.set_temp()

	def crop_free_selection_pixbuf(self, x, y, width, height):
		"""Reduce the size of the pixbuf generated by "create_free_selection_from_main"
		for usability and performance improvements.
		Before this method, the "selection_pixbuf" is a copy of the main one, but
		is mainly full of alpha, while "selection_x" and "selection_y" are zeros.
		After this method, the "selection_pixbuf" is smaller and coordinates make
		more sense."""
		x = int(x)
		y = int(y)
		width = int(width)
		height = int(height)
		min_w = min(width, self.get_selection_pixbuf().get_width() + x)
		min_h = min(height, self.get_selection_pixbuf().get_height() + y)
		new_pixbuf = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, True, 8, width, height)
		new_pixbuf.fill(0)
		self.get_selection_pixbuf().copy_area(x, y, min_w, min_h, new_pixbuf, 0, 0)
		self.get_image().selection_pixbuf = new_pixbuf
		self.get_image().selection_x = x
		self.get_image().selection_y = y

	def forget_selection(self):
		self.get_image().selection_pixbuf = None
		self.get_image().selection_path = None

	############################################################################

	def build_operation(self):
		if self.get_image().get_selection_pixbuf() is None:
			pixbuf = None
		else:
			pixbuf = self.get_image().get_selection_pixbuf().copy()
		operation = {
			'tool_id': self.id,
			'initial_path': self.temp_path,
			'pixbuf': pixbuf,
			'pixb_x': self.get_image().selection_x,
			'pixb_y': self.get_image().selection_y
		}
		return operation

	def do_tool_operation(self, operation):
		if operation['tool_id'] != self.id:
			return
		self.restore_pixbuf()
		self.get_image().update_history_sensitivity(True)
		if operation['initial_path'] is not None:
			cairo_context = cairo.Context(self.get_surface())
			cairo_context.new_path()
			cairo_context.append_path(operation['initial_path'])
			cairo_context.clip()
			cairo_context.set_operator(cairo.Operator.CLEAR)
			cairo_context.paint()
			cairo_context.set_operator(cairo.Operator.OVER)
		if operation['pixbuf'] is not None:
			cairo_context2 = cairo.Context(self.get_surface())
			Gdk.cairo_set_source_pixbuf(cairo_context2, operation['pixbuf'],
				operation['pixb_x'], operation['pixb_y'])
			cairo_context2.paint()

