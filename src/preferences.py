# preferences.py
#
# Copyright 2019 Romain F. T.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from gi.repository import Gtk, Gio, GLib, Gdk
from .gi_composites import GtkTemplate

SETTINGS_SCHEMA = 'com.github.maoschanz.drawing'

@GtkTemplate(ui='/com/github/maoschanz/drawing/ui/preferences.ui')
class DrawingPrefsWindow(Gtk.Window):
	__gtype_name__ = 'DrawingPrefsWindow'

	content_area = GtkTemplate.Child()
	stack_switcher = GtkTemplate.Child()

	background_color_btn = GtkTemplate.Child()
	devel_switch = GtkTemplate.Child()
	devel_box = GtkTemplate.Child()
	preview_btn = GtkTemplate.Child()
	width_btn = GtkTemplate.Child()
	height_btn = GtkTemplate.Child()
	layout_combobox = GtkTemplate.Child()
	add_alpha_switch = GtkTemplate.Child()

	_settings = Gio.Settings.new('com.github.maoschanz.drawing')

	def __init__(self, is_beta, wants_csd, **kwargs):
		super().__init__(**kwargs)
		self.init_template()
		if wants_csd:
			header_bar = Gtk.HeaderBar(visible=True, show_close_button=True, title=_("Preferences"))
			self.set_titlebar(header_bar)
			self.content_area.remove(self.stack_switcher)
			header_bar.set_custom_title(self.stack_switcher)

		background_rgba = self._settings.get_strv('background-rgba')
		r = float(background_rgba[0])
		g = float(background_rgba[1])
		b = float(background_rgba[2])
		a = float(background_rgba[3])
		color = Gdk.RGBA(red=r, green=g, blue=b, alpha=a)
		self.background_color_btn.set_rgba(color)
		self.background_color_btn.connect('color-set', self.on_background_changed)

		if is_beta:
			self.devel_switch.set_active(self._settings.get_boolean('devel-only'))
			self.devel_switch.connect('notify::active', self.on_devel_changed)
		else:
			self.devel_box.set_visible(False)

		self.add_alpha_switch.set_active(self._settings.get_boolean('add-alpha'))
		self.add_alpha_switch.connect('notify::active', self.on_alpha_changed)

		self.width_btn.set_value(self._settings.get_int('default-width'))
		self.height_btn.set_value(self._settings.get_int('default-height'))
		self.width_btn.connect('value-changed', self.on_width_changed)
		self.height_btn.connect('value-changed', self.on_height_changed)

		self.preview_btn.set_value(self._settings.get_int('preview-size'))
		self.preview_btn.connect('value-changed', self.on_preview_changed)

		self.layout_combobox.append('auto', _("Automatic"))
		self.layout_combobox.append('csd', _("Compact"))
		self.layout_combobox.append('csd-eos', 'elementary OS')
		self.layout_combobox.append('ssd', _("Legacy"))
		self.layout_combobox.append('ssd-menubar', _("Menubar only"))
		self.layout_combobox.append('ssd-toolbar', _("Toolbar only"))
		if is_beta and self._settings.get_boolean('devel-only'):
			self.layout_combobox.append('everything', _("Everything (testing only)"))
		self.layout_combobox.set_active_id(self._settings.get_string('decorations'))
		self.layout_combobox.connect('changed', self.on_layout_changed)

	def on_devel_changed(self, w, a):
		self._settings.set_boolean('devel-only', w.get_active())

	def on_alpha_changed(self, w, a):
		self._settings.set_boolean('add-alpha', w.get_active())

	def on_background_changed(self, w):
		color = self.background_color_btn.get_rgba()
		self._settings.set_strv('background-rgba', [str(color.red), str(color.green), \
			str(color.blue), str(color.alpha)])

	def on_width_changed(self, w):
		self._settings.set_int('default-width', self.width_btn.get_value())

	def on_height_changed(self, w):
		self._settings.set_int('default-height', self.height_btn.get_value())

	def on_preview_changed(self, w):
		self._settings.set_int('preview-size', self.preview_btn.get_value())

	def on_layout_changed(self, w):
		self._settings.set_string('decorations', w.get_active_id())
