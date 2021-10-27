#----------------------------------------------------------------------------------------------
#	Automation Tools: Blender Add-on
#	Camshaft Software
#	Copyright (C) 2021
#----------------------------------------------------------------------------------------------
#	MIT License
#----------------------------------------------------------------------------------------------
#	Permission is hereby granted, free of charge, to any person obtaining a copy
#	of this software and associated documentation files (the "Software"), to deal
#	in the Software without restriction, including without limitation the rights
#	to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#	copies of the Software, and to permit persons to whom the Software is
#	furnished to do so, subject to the following conditions:
#
#	The above copyright notice and this permission notice shall be included in all
#	copies or substantial portions of the Software.
#
#	THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#	IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#	FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#	AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#	LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#	OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE#	SOFTWARE.
#---------------------------------------------------------------------------------------------

bl_info = {
	"name": "Automation Tools",
	"description": "Automation Modeling, Rigging and Skinning Tools",
	"author": "Camshaft Software",
	"version": (1, 0, 5),
	"blender": (2, 92, 0),
	"location": "Sidebar -> Automation Tools",
	"url": "https://github.com/AutomationStaff/AutomationTools",
    "wiki_url": "https://github.com/AutomationStaff/AutomationTools/wiki",
	"category": "3D View"
}
 

if "bpy" in locals():
	import importlib
	importlib.reload(ui)
	importlib.reload(modeling)
	importlib.reload(generators)
	importlib.reload(rigging_skinning)
	importlib.reload(export)
else:
	from . import(
		ui,
		modeling,
		generators,
		rigging_skinning,
		export
	)

import bpy
from bpy.utils import register_class, unregister_class

modules = (
	ui,
	modeling,
	generators,
	rigging_skinning,
	export
	)

def register():
	for mod in modules:
		mod.register()

def unregister():
	for mod in reversed(modules):
		mod.unregister()
