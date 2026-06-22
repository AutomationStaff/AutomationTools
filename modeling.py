import bpy
import os
from bpy.utils import register_class, unregister_class
from bpy.types import Operator, Panel, Menu
import bmesh
import json
import math
from mathutils import Vector, Matrix, Euler, Quaternion, Color
import mathutils.geometry
from random import random, uniform
from . rigging_skinning import _class_method_mesh_, go_back_to_initial_mode
from io import StringIO
import subprocess
import platform
import copy
import re

class CopyApplyModifier (Operator):
	bl_idname = "view3d.copy_apply_modifier"
	bl_label = "Duplicate Apply Shrinkwrap"
	bl_description = "Duplicate and apply modifiers"
	bl_options = {'REGISTER', 'UNDO'}

	only_active : bpy.props.BoolProperty(name="Active only", default=True)

	@classmethod
	def poll(cls, context):
		return context.object is not None and context.object.modifiers and context.object.data.shape_keys is None

	def doCopyApplyModifier(self, mods_stack, o, obj):
		# get shrinkwrap modifiers
		if obj.modifiers.active.type == 'SHRINKWRAP':
			if mods_stack:
				for m in mods_stack:
					mod = m.type
					# find modifier
					if mod == 'SHRINKWRAP' and m.show_viewport:
						name = m.name
						o.modifier_copy(modifier = name)
						o.modifier_apply(modifier = obj.modifiers.active.name)
						obj.modifiers.active = m

						# check result
						if name not in obj.modifiers[:]:
							self.report({'INFO'},  ("Finished"))
						else:
							self.report({'INFO'},  ("Nothing changed"))

	def execute(self, context):
		obj = bpy.context.object
		o = bpy.ops.object
		context_mode = ''

		if obj and obj.type == 'MESH':
			mods_stack = []

		if context.mode == 'EDIT_MESH':
			context_mode = 'OBJECT'
			o.mode_set(mode = 'OBJECT')

		if self.only_active:
			a_mod = obj.modifiers.active
			if a_mod:
				mods_stack.append(a_mod)
				self.doCopyApplyModifier(mods_stack, o, obj)
		else:
			mods_stack = obj.modifiers[:]
			if mods_stack:
				self.doCopyApplyModifier(mods_stack, o, obj)

		if context_mode == 'OBJECT':
			o.mode_set(mode = 'EDIT')

		return {'FINISHED'}

class ToggleModifiersByType(Operator):
	bl_idname = "view3d.toggle_modifiers_by_type"
	bl_label = "Toggle Modifiers By Type"
	bl_description = 'Toggle Modifiers by Type'	
	mod_type: bpy.props.EnumProperty(items=[
		('NONE', 'NONE', '', 0),		
		('MIRROR', 'MIRROR', '', 1),
		('SUBSURF', 'SUBSURF', '', 3),	
		('SOLIDIFY', 'SOLIDIFY', '', 4),			
		('SHRINKWRAP', 'SHRINKWRAP', '', 5),
		('BEVEL', 'BEVEL', '', 6),
		('ARRAY', 'ARRAY', '', 7),
		('DECIMATE', 'DECIMATE', '', 8),
		('CURVE', 'CURVE', '', 9)
		],
		name='Modifier type', default='NONE')

	@classmethod
	def poll(cls, context):
		return context.object is not None

	def ToggleModifiers (self, mods_stack):
		if len(mods_stack):
			for m in mods_stack:
				if m.type == self.mod_type:
					if m.show_viewport == True:
						m.show_viewport = False
					else:
						m.show_viewport = True

		else:
			self.report({'WARNING'}, "[Error]: Mesh has no Modifiers")

	def execute(self, context):
		sel = [obj for obj in context.selected_objects if obj.type == 'MESH']
		if sel:
			for o in sel:
				mods_stack = o.modifiers[:]
				self.ToggleModifiers(mods_stack)

		return {'FINISHED'}

class ToggleAllModifiersVisibility(Operator):
	bl_idname = "view3d.toggle_all_modifiers_visibility"
	bl_label = "Toggle All Modifiers"
	bl_description = "Toggle All Modifiers Visibility in Viewport"

	@classmethod
	def poll(cls, context):
		return context.object is not None

	def get_hidden_modifiers(self, obj):
		hidden = [mod.name for mod in obj.modifiers if mod.show_viewport == False]
		return hidden

	def getAllModifiers(self, obj):
		if obj and obj.type == "MESH":
			modifiers_list = obj.modifiers[:]
			if len(modifiers_list):
				return modifiers_list

	def hideAllModifiers(self, mod):
		if mod:
			for n in mod:
				n.show_viewport = False

	def showAllModifiers(self, mod):
		if mod:
			for n in mod:
				n.show_viewport = True

	def execute(self, context):
		obj = bpy.context.object
		sel = []
		sel = bpy.context.selected_objects
		if len(sel) < 1:
			sel.append(obj)

		# get hidden
		hidden_modifiers_list = []
		if 'hidden_modifiers' in obj:
			hidden_modifiers_list = obj['hidden_modifiers']

		# store hidden modifiers
		if 'hidden_modifiers' not in obj:
			obj['hidden_modifiers'] = ""
		obj['hidden_modifiers'] = self.get_hidden_modifiers(obj)

		visible = bpy.context.scene.modifiersVisibilityStateAll
		if visible:
			if sel:
				for obj in sel:
					mod = self.getAllModifiers(obj)
					if mod:
						self.hideAllModifiers(mod)
			bpy.context.scene.modifiersVisibilityStateAll = False
			#bpy.context.space_data.overlay.show_overlays = True
		else:
			if sel:
				for obj in sel:
					mod = self.getAllModifiers(obj)
					if mod:
						self.showAllModifiers(mod)
			bpy.context.scene.modifiersVisibilityStateAll = True
			# bpy.context.space_data.overlay.show_overlays = False

		# hide if was hidden
		for mod in obj.modifiers:
			if mod.name in hidden_modifiers_list:
				mod.show_viewport = False


		return {'FINISHED'}

class TransferModifiers(Operator):
	bl_idname = "object.transfer_modifiers"
	bl_label = "Transfer Modifiers"
	bl_description = "Copy the Active Modifier to selected objects. Active Object is the source"
	bl_options = {'REGISTER', 'UNDO'}

	@classmethod
	def poll(cls, context):
		return context.object is not None

	def execute(self, context):
		if (len(bpy.context.selected_objects) > 1 and len(bpy.context.object.modifiers) > 0):
			mod = bpy.context.object.modifiers.active.name
			bpy.ops.object.modifier_copy_to_selected(modifier = mod)
		else:
			self.report({'WARNING'},  "Select at least 2 Objects. Active Object must have an active modifier!")
		return {'FINISHED'}

class AddBevelWidthDriver(Operator):
	bl_idname = "object.add_bevel_width_driver"
	bl_label = "Add Bevel Width Driver"
	bl_description = "Add bevel width driver for Rim scale shape keys"
	bl_options = {'REGISTER', 'UNDO'}

	# bpy.context.object.animation_data.drivers[0].driver.expression = 'var * (3 - 1) + 3'
	@classmethod
	def poll(cls, context):
		return context.object is not None

	def execute(self, context):
		obj = bpy.context.object
		if len(obj.modifiers) > 0 and 'Bevel' in obj.modifiers and obj.data.shape_keys:
			bevel = obj.modifiers["Bevel"]
			keys = obj.data.shape_keys.key_blocks
			val = round(bevel.width, 2)
			if "Scale" in keys:
				if	bevel.offset_type != 'WIDTH':
					bevel.offset_type = 'WIDTH'
				key_id = obj.data.shape_keys.key_blocks.id_data
				fcurve = obj.modifiers['Bevel'].driver_add('width')
				driver = fcurve.driver
				var = driver.variables.new()
				var.name = "var"
				var.type = "SINGLE_PROP"
				if val < 1:
					driver.expression =	 "var * (1 - " + str(val) + ") + " + str(val)
				else:
					driver.expression =	 "var * (" + str(val) + " - 1) + " + str(val)
				target = var.targets[0]
				target.id_type = 'KEY'
				target.id = key_id
				target.data_path = 'key_blocks["Scale"].value'

				#create a bevel width property
				rna_ui = obj.get('_RNA_UI')
				if rna_ui is None:
					obj['_RNA_UI'] = {}
					rna_ui = obj['_RNA_UI']

				obj["bevel_width_driver"] = val
				rna_ui["bevel_width_driver"] = {
												"description":"Bevel Width Driver Value",
												"default": 0.0,
												"min":0.0,
												"soft_min":0.0
												}

				#else:
				#	obj['bevel_width_driver'] = val


			else:
				self.report({'WARNING'},  "Scale Shape Key not found!")
		else:
			self.report({'WARNING'},  "Bevel Modifier/Shape Keys not found!")
		return {'FINISHED'}

class BevelWidthLerpInputBar(Operator):
	bl_idname = "object.bevel_width_input_bar"
	bl_label = "Bevel Width Driver"
	bl_description = "Bevel Width Driver"
	bl_options = {'REGISTER', 'UNDO'}

	@classmethod
	def poll(cls, context):
		return context.object is not None and len(context.object.modifiers) > 0 and 'Bevel' in context.object.modifiers and len(context.object.animation_data.drivers) > 0

	def execute(self, context):
		obj = bpy.context.object
		val = round(obj['bevel_width_driver'], 2)
		drv = obj.animation_data.drivers[0].driver
		## negative value is not allowed
		#if val < 0:
		#	val = 0
		#	obj['bevel_width_driver'] = 0

		if val < 1:
			drv.expression =  "var * (1 - " + str(val) + ") + " + str(val)
		else:
			drv.expression =  "var * (" + str(val) + " - 1) + " + str(val)

		return {'FINISHED'}

class ApplyModifierShapeKeys(Operator):
	bl_idname = "object.apply_modifiers_with_shape_keys"
	bl_label = "Apply Modifier [Shape Keys]"
	bl_description = "Apply active (Mirror/Shrinkwrap/Triangulate/Weighted_Normal) modifier on the mesh with shape keys. Applying a geometric modifier such as Mirror leads to applying Shrinkwrap, Array, Bevel automatically."

	@classmethod
	def poll(cls, context):
		return context.object is not None and context.object.type == 'MESH' and context.object.data.shape_keys and context.mode == 'OBJECT'

	def duplicate_body(self, obj):
			bpy.ops.object.duplicate()
			src_shape_key = bpy.context.object
			src_shape_key.name =  obj.name + "_shape_key_mesh"
			bpy.ops.object.select_all(action='DESELECT')
			return src_shape_key

	def get_shape_key_id_by_name(self, obj, active_shape_key):
		keys = obj.data.shape_keys.key_blocks.keys()
		k = 0
		for i in keys:
			if i == active_shape_key:
				break
			else:
				k += 1
		return k

	def convert_active_shape_key_to_mesh(self, obj, ks, active_shape_key):
		ops = bpy.ops.object
		active = obj.active_shape_key
		index = obj.active_shape_key_index

		#get key shapes list
		if obj.data.shape_keys:
			keys = obj.data.shape_keys.key_blocks[:]
			#remove shape keys the active last
			ind = None
			for i in keys:
				if i.name != 'Basis':
					if i.value != 1.0:
						i.value = 1.0
				if i != ks:
					#get [i] index
					ind = self.get_shape_key_id_by_name(obj, i.name)
					#set [i] active
					obj.active_shape_key_index = ind
					#delete
					ops.shape_key_remove(all=False)
			#get clean mesh
			bpy.context.view_layer.objects.active = obj
			obj.select_set(True)
			# convert is a straightforward way to get all modifiers applied
			ops.shape_key_remove(all=False)
			bpy.ops.object.convert(target='MESH')

	def apply_modifiers_shape_keys(self, obj, ops, modifier, obj_name):
		if modifier.type != 'ARMATURE':
			active_shape_key = bpy.context.object.active_shape_key.name
			#duplicate
			src_shape_key = self.duplicate_body(obj)

			#remove all shape keys from the target
			bpy.context.view_layer.objects.active = obj
			ops.shape_key_remove(all=True)

			#apply active modifier
			ops.modifier_apply(modifier = modifier.name)

			#add base shape key
			ops.shape_key_add(from_mix=False)

			#transfer shape keys from the backup mesh
			src_shape_key.select_set(True)
			keys = src_shape_key.data.shape_keys.key_blocks[:]

			count = len(keys)
			for i in range(1, count):
				src_shape_key.active_shape_key_index = i
				bpy.ops.object.shape_key_transfer()

			#clean up
			ops.select_all(action='DESELECT')

			if src_shape_key:
				bpy.data.objects.remove(src_shape_key, do_unlink=True)

			if obj_name in bpy.data.objects:
				obj.select_set(True)
				bpy.context.view_layer.objects.active = obj

	def extract_key_shape_meshes(self, obj):
		key_blocks = obj.data.shape_keys.key_blocks[:]
		mesh_list=[]
		#extract meshes
		for i in range(1, len(key_blocks)):
			obj.select_set(True)
			bpy.context.view_layer.objects.active = obj

			self.duplicate_body(obj)
			obj.select_set(False)

			o = bpy.context.object
			o.active_shape_key_index = i
			ks = o.active_shape_key
			active_shape_key = o.active_shape_key.name

			o.name = key_blocks[i].name

			mesh_list.append(o)

			bpy.context.view_layer.objects.active = o
			self.convert_active_shape_key_to_mesh(o, ks, key_blocks[i].name)

			bpy.ops.object.select_all(action='DESELECT')
		return mesh_list

	def validate_shape_keys(self, vertex_count):
		for i in vertex_count:
			if i == vertex_count[0]:
				continue
			else:
				return False

	def execute(self, context):
		data = bpy.data.objects
		obj = bpy.context.object
		obj_name = obj.name
		ops = bpy.ops.object
		modifier = obj.modifiers.active		
		ks = obj.active_shape_key

		if ks is None:
			ks = obj.data.shape_keys.key_blocks[0]
			obj.active_shape_key_index = 0

		active_shape_key = obj.active_shape_key.name
		bpy.context.view_layer.objects.active = obj
		indicies = get_faces_indicies(self, obj)
		if obj is not None:
			if obj.select_get() == False:
				obj.select_set(True)

			# if vertex count is not changed
			vertex_count_change = ('MIRROR', 'ARRAY', 'BEVEL')
			vertex_count_nochange = ('TRIANGULATE', 'SHRINKWRAP', 'ARMATURE', 'WEIGHTED_NORMAL', 'NODES')

			#forced order (exec?)
			if len(obj.modifiers):
				for m in obj.modifiers:
					if m.type == 'MIRROR':
						ops.modifier_move_to_index(modifier = m.name, index = 0)
					if m.type == 'ARRAY':
						if 'Mirror' in obj.modifiers:
							ops.modifier_move_to_index(modifier = m.name, index = 1)
						else:
							ops.modifier_move_to_index(modifier = m.name, index = 0)
					if m.type == 'BEVEL':
						if 'Mirror' in obj.modifiers and 'Array' in obj.modifiers:
							ops.modifier_move_to_index(modifier = m.name, index = 2)
						elif 'Mirror' or 'Array' in obj.modifiers:
							ops.modifier_move_to_index(modifier = m.name, index = 1)
						else:
							ops.modifier_move_to_index(modifier = m.name, index = 0)

					if m.type == 'ARMATURE':
						ops.modifier_move_to_index(modifier = m.name, index = (len(obj.modifiers)-1))


			if 'Mirror' in obj.modifiers:
				if modifier.type != 'MIRROR' and modifier.type in vertex_count_change:
					modifier = obj.modifiers['Mirror']

			if modifier.type in vertex_count_nochange:
				self.apply_modifiers_shape_keys(obj, ops, modifier, obj_name)
				if obj.data.shape_keys is not None:
					obj.active_shape_key_index = 0

			elif modifier.type in vertex_count_change:
				active = obj
				active.select_set(True)

				#delete unsupported modifiers
				for m in obj.modifiers:
					if m.type not in vertex_count_nochange and m.type not in vertex_count_change:
						bpy.ops.object.modifier_remove(modifier = m.name)

				# apply shrinkwraps if found
				for m in obj.modifiers:
					if m.type == 'SHRINKWRAP':
						obj.modifiers.active = obj.modifiers[m.name]
						mod = obj.modifiers[m.name]
						self.apply_modifiers_shape_keys(obj, ops, mod, obj_name)

						bpy.ops.object.select_all(action='DESELECT')
						if obj_name in data:
							obj.select_set(True)
							bpy.context.view_layer.objects.active = obj
				obj.modifiers.active = modifier

				# modifiers tweaks
				#if modifier.type == 'ARRAY':
				#	if modifier.use_merge_vertices:
				#		modifier.use_merge_vertices = False

				if modifier.type == 'ARRAY':
					if modifier.use_merge_vertices_cap == False:
						modifier.use_merge_vertices_cap = True

				if modifier.type == 'MIRROR':
					if modifier.use_mirror_v == False:
						modifier.use_mirror_v = True

				# unpack shape key meshes
				extracted_shape_key_meshes = self.extract_key_shape_meshes(obj)

				# delete shape keys from obj
				obj.select_set(True)
				bpy.context.view_layer.objects.active = obj
				bpy.ops.object.shape_key_remove(all=True)

				# get all shape key meshes
				obj_list = [o for o in extracted_shape_key_meshes]
				obj_list.insert(0, obj)

				# apply modifiers
				if modifier.type in vertex_count_change:					
					for m in obj.modifiers:
						if m.type in vertex_count_change:
							# if Mirror
							if m.type == 'MIRROR':
								ops.modifier_apply(modifier = 'Mirror')
								obj.select_set(True)
								fix_mirrored_half_triangulation(self, obj, indicies)
							else:
								ops.modifier_apply(modifier = m.name)

				# vertex count of shape key meshes
				shape_keys_names = [vc.name for vc in obj_list]
				shape_keys_names[0] = "Basis"
				vertex_count = [len(vc.data.vertices) for vc in obj_list]
				valid = self.validate_shape_keys(vertex_count)

				# console info
				print("----------------------------------------------------------------------------------------------------------------------")
				print("Automation Tools: object.apply_modifiers_with_shape_keys")
				info = dict(zip(shape_keys_names, vertex_count))
				if valid == False:
					self.report({'WARNING'}, (obj.name + " " + str(info) + " *** ERROR: Unequal vertex count!" ))
				else:
					print (obj.name + " " + str(info) + " *** OK")
				print("----------------------------------------------------------------------------------------------------------------------")

				# flag to disable export if wrong vertex count
				if valid == False:
					bpy.context.scene.export_flag = False

				#add a base shape key
				bpy.context.view_layer.objects.active = obj
				bpy.ops.object.shape_key_add(from_mix=False)

				#apply modifiers on the extracted meshes
				for o in extracted_shape_key_meshes:
					bpy.ops.object.select_all(action='DESELECT')
					o.select_set(True)
					bpy.context.view_layer.objects.active = o
					for m in o.modifiers[:]:
						if m.type != 'ARMATURE':
							ops.modifier_apply(modifier = m.name)

				# rebuild key shapes
				for o in obj_list:
					o.select_set(True)
				bpy.context.view_layer.objects.active = obj
				bpy.ops.object.join_shapes()

				if obj.data.shape_keys is not None:
					obj.active_shape_key_index = 0

				# cleanup
				bpy.ops.object.select_all(action='DESELECT')
				for o in extracted_shape_key_meshes:
					data.remove(o, do_unlink=True)

				if obj.name in data:
					obj.select_set(True)
					bpy.context.view_layer.objects.active = obj

				# fix broken shape names:
				for shape in obj.data.shape_keys.key_blocks[:]:
					if '.' in shape.name:
						shape.name = shape.name.split('.')[0]

			else:
				self.report({'WARNING'},  "Only Mirror, Array, Bevel, Triangulate, Shrinkwrap, Weighted_Normal modifiers can be applied!")

		return {'FINISHED'}

class RotateEdgeTriangulationQuads(Operator):
	bl_idname = "mesh.rotate_edge_triangulation_quads"
	bl_label = "Rotate quad diagonal Edge in Triangulation Modifier"
	bl_description = 'Non-destructive Triangulate modifier edge rotation. Requires face selection. Use both - Beauty (Same Direction) and Fixed (Flip Direction) methods for fixing mesh triangulation.'
	quad_method : bpy.props.StringProperty()

	@classmethod
	def poll(cls, context):
		return context.object is not None and context.object.modifiers is not None and 'Triangulate' in context.object.modifiers and bpy.context.mode == 'EDIT_MESH'

	def update(self, bm, obj):
			bm.select_flush(True)
			bmesh.update_edit_mesh(obj.data)

	def execute(self, context):
		obj = bpy.context.object
		qm = obj.modifiers["Triangulate"].quad_method
		bm = bmesh.from_edit_mesh(obj.data)

		#get init edges
		init_edges = [e for e in bm.edges]

		if qm == 'FIXED':
			qm = self.quad_method
			bpy.ops.mesh.quads_convert_to_tris(quad_method = qm)
			#bpy.ops.mesh.select_all(action='DESELECT')

			self.update(bm, obj)

			new_edges = [e for e in bm.edges if e not in init_edges ]

			#dissolve new edges
			bmesh.ops.dissolve_edges(bm, edges = new_edges, use_verts = False, use_face_split = False)
			bpy.context.tool_settings.mesh_select_mode = (False, False, True)
			self.update(bm, obj)

			# reset normals
			bm.normal_update()
			bpy.ops.object.reset_normals_object()


		else:
			self.report({'WARNING'},  "Select 'Fixed' Quad Method in the Triangulate Modifier options!")

		return {'FINISHED'}

class LightsUnwrap(Operator):
	bl_label = "Lights UVs"
	bl_idname = "object.lights_unwrap"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = 'Unwrap Lights for Material Assignment. Select Polygons/Vertices and press the Button.'
	U : bpy.props.FloatProperty(name="U_coord", options = {'HIDDEN'})
	V : bpy.props.FloatProperty(name="V_coord", options = {'HIDDEN'})

	@classmethod
	def poll(cls, context):
		return context.mode == "EDIT_MESH"

	def execute(self, context):		
		ResetUVSelection(self, context)
		bpy.ops.mesh.mark_seam(clear=True)

		if_sync_select = bpy.context.scene.tool_settings.use_uv_select_sync

		if bpy.context.active_object:
			bpy.context.area.type = 'IMAGE_EDITOR'

			bpy.ops.uv.unwrap(method='ANGLE_BASED', margin=0.001)
			bpy.context.area.ui_type = 'UV'

			if not if_sync_select:
				bpy.context.scene.tool_settings.use_uv_select_sync	= True

			bpy.context.space_data.cursor_location[0] = self.U
			bpy.context.space_data.cursor_location[1] = self.V

			bpy.ops.uv.snap_selected(target='CURSOR')

			bpy.context.area.type = 'VIEW_3D'

			bpy.context.scene.tool_settings.use_uv_select_sync	= if_sync_select

			bpy.ops.mesh.at_mark_seams()

		return {'FINISHED'}

class UVSeamsFromHardEdges(Operator):
	bl_label = "UV Seams from Hard Edges"
	bl_idname = "mesh.uv_seams_from_hard_edges"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = 'Create UV Seams based on mesh Hard Edges'

	@classmethod
	def poll(cls, context):
		return context.mode == "EDIT_MESH"

	def execute(self, context):
		obj = bpy.context.object

		bm = bmesh.from_edit_mesh(obj.data)
		#get selection
		sel = [f for f in bm.edges if f.select]
		faces = [f for f in bm.faces if f.select]
		edges = []
		if sel:
			edges = sel
		else:
			edges = bm.edges

		bpy.ops.mesh.select_all(action='DESELECT')
		hard_edges = [e for e in edges if e.smooth == False]
		for i in hard_edges:
			i.select_set(True)
		bpy.ops.mesh.mark_seam(clear=False)

		for i in hard_edges:
			i.select_set(False)
		for e in edges:
			e.select_set(False)

		if len(faces) > 0:
			for f in faces:
				f.select_set(True)
		return {'FINISHED'}

class AT_MarkSeams(Operator):
	bl_idname = "mesh.at_mark_seams"
	bl_label = "Mark Seams"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = "Mark Seams. Face selection: Mark borders, Edge/Vertex selection: Mark Edges"

	@classmethod
	def poll(cls, context):
		return context.object is not None

	def execute(self, context):
		sel = None
		bm = None

		select_mode = context.tool_settings.mesh_select_mode[:]

		if context.tool_settings.mesh_select_mode[2]:
			bm = bmesh.from_edit_mesh(bpy.context.object.data)
			sel = [f for f in bm.faces if f.select]			
			bpy.ops.mesh.region_to_loop()

		bpy.ops.mesh.mark_seam(clear=False)

		if sel is not None:
			for f in sel:
				f.select_set(True)

		if context.tool_settings.mesh_select_mode != select_mode:
			context.tool_settings.mesh_select_mode = select_mode
		
		if bm is not None:
			bm.free()

		return {'FINISHED'}

class AT_UVUnwrap(Operator):
	bl_idname = "mesh.at_uv_unwrap"
	bl_label = "UV Unwrap"
	bl_description = "UV Unwrap"	
	bl_options = {'REGISTER', 'UNDO'}

	texel: bpy.props.FloatProperty(min=0.0, default=50.0, name='Texel Density:', options = {'SKIP_SAVE'})

	@classmethod
	def poll(cls, context):
		return context.object is not None and context.mode == "EDIT_MESH"

	def execute(self, context):
		if bpy.context.scene.tool_settings.use_uv_select_sync == False:
			bpy.context.scene.tool_settings.use_uv_select_sync = True

		sel = bpy.context.selected_objects
		bpy.ops.object.mode_set(mode = 'OBJECT')
		bpy.ops.object.select_all(action='DESELECT')

		for obj in sel:
			if obj.type == "MESH":
				obj.select_set(True)
				bpy.context.view_layer.objects.active = obj
				bpy.ops.object.mode_set(mode = 'EDIT')

				bpy.ops.uv.unwrap(method='ANGLE_BASED', margin=0.001, correct_aspect = False)
				bpy.ops.uv.seams_from_islands()

				if context.scene.apply_uv_scale:
					bpy.ops.mesh.scale_uvs(command='SET', texel=self.texel)

				bpy.ops.object.mode_set(mode = 'OBJECT')
				bpy.ops.object.select_all(action='DESELECT')

		for o in sel:
			o.select_set(True)
		bpy.ops.object.mode_set(mode = 'EDIT')

		return {'FINISHED'}

class SnapUVBottomsUVs(Operator):
	bl_idname = "mesh.snap_bottom_uvs"
	bl_label = "Snap Body Bottom UVs"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = "Snap Body Bottom UVs"

	@classmethod
	def poll(cls, context):
		return context.object is not None and bpy.context.object.mode == "EDIT" and context.mode == "EDIT_MESH"

	def get_vertex_uvs(self, v, uv_layer):
		for loop in v.link_loops:
			uvs = loop[uv_layer]
		return uvs

	def get_edge_uvs(self, edge, uv_layer):
		uvs = []
		uvs.append(cls.get_vertex_uvs(edge.verts[0]), uv_layer)
		uvs.append(cls.get_vertex_uvs(edge.verts[1]), uv_layer)
		return uvs

	def execute(self, context):
		obj = bpy.context.active_object.data
		bm = bmesh.from_edit_mesh(obj)
		uv_layer = bm.loops.layers.uv.verify()

		uvs = dict()
		for face in bm.faces:
			for loop in face.loops:
				if loop.vert not in uvs:
					uvs[loop.vert] = [loop[uv_layer]]
				else:
					uvs[loop.vert].append(loop[uv_layer])

		for vert in uvs:
			for uv_loop in uvs[vert]:
				if vert.select:
					for e in vert.link_edges:
						if not e.select:
							v0 = self.get_vertex_uvs(e.verts[0], uv_layer)
							v1 = self.get_vertex_uvs(e.verts[1], uv_layer)

							dist1 = (uv_loop.uv - v0.uv).length
							dist2 = (uv_loop.uv - v1.uv).length

							if dist1 > dist2:
								uv_loop.uv = v0.uv
							else:
								uv_loop.uv = v1.uv

							bmesh.update_edit_mesh(obj)
		return {'FINISHED'}

def ResetUVSelection(cls, context):	
	mesh = bpy.context.object.data
	bm = bmesh.from_edit_mesh(mesh)
	sel = [f for f in bm.faces if f.select]
	tool_settings = context.scene.tool_settings
	#select all and unpin
	for f in bm.faces:
		f.select = True
	
	if tool_settings.use_uv_select_sync:
		tool_settings.use_uv_select_sync = False	
		bpy.ops.uv.select_all(action='DESELECT')
		tool_settings.use_uv_select_sync = True
	else:		
		bpy.ops.uv.select_all(action='DESELECT')

	#back to original selection
	for f in bm.faces:
		f.select = False	

	if sel is not None:
		for f in sel:
			f.select = True
	
	if bm is not None:
		bm.free()


class ScaleUVs(Operator):
	bl_label = "Scale Selected UVs"
	bl_idname = "mesh.scale_uvs"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = "Scale Selected UVs: 1 cm = 128x128 pix"
	command: bpy.props.StringProperty(options={'HIDDEN'})
	texel: bpy.props.FloatProperty(min=0.0, default=50.0, options={'SKIP_SAVE'})
	
	@classmethod
	def poll(cls, context):
		return context.object is not None and context.mode == "EDIT_MESH"

	def scale_XY(self, v, s, p):
		return (p[0] + s[0]*(v[0] - p[0]), p[1] + s[1]*(v[1] - p[1]))

	def uv_scale(self, uv_layer, uv_map, scale):
		bpy.ops.object.mode_set(mode = 'EDIT')
		obj = bpy.context.object
		bm = bmesh.from_edit_mesh(obj.data)
		bm.select_flush_mode()
		bmesh.update_edit_mesh(obj.data)
		uv_layer = bm.loops.layers.uv.active

		#get selected uvs and coordinates
		selected_uv_verts = []
		coordinates = []
		for f in [face for face in bm.faces if face.select]:			
			for loop in f.loops:
				uv_data = loop[uv_layer]
				if f.uv_select and uv_data.pin_uv == False:
					selected_uv_verts.append(uv_data)
					coordinates.append(uv_data.uv)

		# get pivot
		pivot = Vector ((0.0, 0.0))
		for v in coordinates:
			pivot += v

		if pivot[0] != 0 and  pivot[1] != 0:
			pivot = pivot/len(coordinates)
		else:
			pivot = ((0.5, 0.5))

		for uv in selected_uv_verts:
			uv.uv = self.scale_XY(uv.uv, scale, pivot)

		if bm is not None:
			bm.free()

	def uv_from_vert_first(self, uv_layer, v, f):
		for loop in v.link_loops:
			if loop.face == f:
				uv_data = loop[uv_layer]
				return uv_data.uv

	def get_triangle_perimeter(self, verts):
		perimeter = 0
		l1 = (verts[0].co - verts[1].co).length
		l2 = (verts[1].co - verts[2].co).length
		l3 = (verts[0].co - verts[2].co).length
		perimeter = (l1 + l2 + l3)
		return perimeter

	def get_current_ratio(self, obj):
		bpy.ops.object.mode_set(mode = 'OBJECT')
		bpy.ops.object.select_all(action='DESELECT')

		if obj.type == 'MESH':
			obj.select_set(True)
			bpy.context.view_layer.objects.active = obj
			bpy.ops.object.mode_set(mode = 'EDIT')

			#obj = context.object
			if len(obj.data.uv_layers.keys()) > 0:
				bm = bmesh.from_edit_mesh(obj.data)
				bpy.ops.uv.average_islands_scale()

				uv_layer = bm.loops.layers.uv.active

				uv_face_list = []
				for face in bm.faces:
					if face.uv_select:
						uv_face_list.append(face)

				if len(uv_face_list):

					# get the biggest face
					areas = [f.calc_area() for f in uv_face_list]

					max_val = max(areas)
					ind =  areas.index(max_val)

					f = uv_face_list[ind]

					verts = [v for v in f.verts]

					verts = verts[:3]
					face_perimeter = self.get_triangle_perimeter(verts)

					coord1 = self.uv_from_vert_first(uv_layer, verts[0], f)
					coord2 = self.uv_from_vert_first(uv_layer, verts[1], f)
					coord3 = self.uv_from_vert_first(uv_layer, verts[2], f)

					#loops
					v0 = [loop for loop in (verts[0].link_loops[:])]
					v1 = [loop for loop in (verts[1].link_loops[:])]
					v2 = [loop for loop in (verts[2].link_loops[:])]

					uv_edge_length_1 = (coord1 - coord2).length
					uv_edge_length_2 = (coord2 - coord3).length
					uv_edge_length_3 = (coord1 - coord3).length

					face_uv_perimeter = (uv_edge_length_1 + uv_edge_length_2 + uv_edge_length_3)

					if face_uv_perimeter and face_perimeter > 0:
						current_ratio = face_uv_perimeter/face_perimeter
						return (current_ratio, uv_layer)
					else:
						self.report({'WARNING'},  "Texel cannot be measured! Check UV zero values")
						return None

				if bm is not None:
					bm.free()

				else:
					self.report({'WARNING'},  "Selection update is required. Select UVs manually in the UV Editor.")
			else:
				self.report({'WARNING'},  "UVMap not found!")

	def execute(self, context):
		ResetUVSelection(self, context)
		if_sync = False
		if bpy.context.scene.tool_settings.use_uv_select_sync:
			if_sync = True
			bpy.ops.uv.pin(clear=False)
			context.scene.tool_settings.use_uv_select_sync = False
			context.scene.tool_settings.uv_select_mode='VERTEX'
			bpy.ops.uv.select_pinned()
			bpy.ops.uv.pin(clear=True)

		sel = bpy.context.selected_objects

		for obj in sel:
			if self.command == "SET":
				ratio_uvlayer = self.get_current_ratio(obj)
				if ratio_uvlayer is not None:
					current_ratio = ratio_uvlayer[0]
					texel = self.texel if self.texel != 50.0 else context.scene.texel_value					
					#ratio_coef = texel/current_ratio
					uv_layer = ratio_uvlayer[1]
					#unit = bpy.context.scene.unit_settings.scale_length
					#uv_scale_coef = unit * 100
					if current_ratio > 0:
						s = texel/current_ratio
						bpy.ops.object.mode_set(mode = 'OBJECT')

						#scale UVs
						map_name = obj.data.uv_layers.keys()
						uv_map = obj.data.uv_layers[map_name[0]]
						self.uv_scale(uv_layer, uv_map, (s, s))

						bpy.ops.object.mode_set(mode = 'OBJECT')
						bpy.ops.object.select_all(action='DESELECT')

			elif self.command == "GET":
				if self.get_current_ratio(obj) is not None:
					bpy.context.scene.texel_value = self.get_current_ratio(obj)[0]

		#cleanup
		for o in sel:
			o.select_set(True)
		bpy.ops.object.mode_set(mode = 'EDIT')

		bpy.ops.uv.select_all(action='DESELECT')

		if if_sync == True:
			bpy.context.scene.tool_settings.use_uv_select_sync = True

		return {'FINISHED'}

class UnwrapCylinder(Operator):
	bl_idname = "mesh.unwrap_cylinder"
	bl_label = "Unwrap Cylinder"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = "Unwrap Cylinder"

	@classmethod
	def poll(cls, context):
		return context.object is not None and context.mode == "EDIT_MESH"

	def execute(self, context):
		obj = bpy.context.object
		bm = bmesh.from_edit_mesh(obj.data)

		if bm.select_mode != 'FACE':
			bm.select_mode = {'FACE'}

		top_faces = [f for f in bm.faces if f.select]
		bpy.ops.mesh.select_all(action='DESELECT')

		ortho_faces = []
		if len(top_faces):
			top_normal = top_faces[0].normal

		for f in bm.faces:
			if f.normal == top_normal:
				top_faces.append(f)
			else:
				ortho_faces.append(f)

		ortho_edge = None
		for f in ortho_faces:
			for v in f.verts:
				if (v.normal.dot(top_normal) == 0):
					v.select = True

		bm.select_flush_mode()
		bmesh.update_edit_mesh(obj.data)
		bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')

		return {'FINISHED'}

class UnwrapPipe(Operator):
	bl_idname = "mesh.unwrap_pipe"
	bl_label = "Unwrap Pipe"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = "Unwrap Pipe"

	@classmethod
	def poll(cls, context):
		return context.object is not None

	def execute(self, context):
		bpy.ops.object.mode_set(mode = 'EDIT')
		bpy.ops.mesh.select_all(action='DESELECT')
		obj = bpy.context.object
		bm = bmesh.from_edit_mesh(obj.data)

		if bm is not None:
			bm.verts.ensure_lookup_table()
			v = bm.verts[0]

			edges = v.link_edges
			for e in edges:
				e.select_set(True)

			bm.select_flush_mode()
			bmesh.update_edit_mesh(obj.data)

			bm.select_mode = {"EDGE"}

			bpy.ops.mesh.loop_multi_select(ring=False)
			bpy.ops.mesh.mark_seam(clear=False)

			bpy.ops.mesh.uv_seams_from_hard_edges()

			bpy.ops.mesh.select_all(action='SELECT')

			bpy.ops.mesh.at_uv_unwrap()
		
		else:			
			self.report({'WARNING'},  obj.name + " has no geometry")

		return {'FINISHED'}

class CreateUVChecker(Operator):
	bl_idname = "object.add_uv_checker"
	bl_label = "Assign UV Checker"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = "Assign UV Checker"

	@classmethod
	def poll(cls, context):
		return context.object is not None and context.object.active_material is not None

	def execute(self, context):
		checker_path = os.path.join(os.path.dirname(__file__),'images/checker_1.png')
		bpy.ops.image.open(filepath = checker_path)

		material = bpy.context.object.active_material
		if	material.use_nodes == False:
			material.use_nodes = True

		shader = None
		if bpy.context.object.active_material.node_tree is not None:
			if 'Principled BSDF' in bpy.context.object.active_material.node_tree.nodes:
				shader = bpy.context.object.active_material.node_tree.nodes.get('Principled BSDF')

			if shader is not None:
				texture_node = material.node_tree.nodes.new('ShaderNodeTexImage')
				texture_node.image = bpy.data.images['checker_1.png']

				mapping_node = material.node_tree.nodes.new('ShaderNodeMapping')
				coord_node = material.node_tree.nodes.new('ShaderNodeTexCoord')

				nodes = [texture_node, mapping_node, coord_node]

				value = 200
				for node in nodes:
					node.select = False
					node.location[0] -= value
					value += value

				texture_node.label = 'Checker'
				#link nodes
				material.node_tree.links.new(texture_node.outputs[0], shader.inputs[0])
				material.node_tree.links.new(mapping_node.outputs[0], texture_node.inputs[0])
				material.node_tree.links.new(coord_node.outputs[2], mapping_node.inputs[0])

				bpy.context.space_data.shading.color_type = 'TEXTURE'
		else:
			self.report({'WARNING'},  "Principled BSDF is required! Activate Shader Nodes if they are not used")

		return {'FINISHED'}

class ToggleUVChecker(Operator):
	bl_idname = "mesh.show_uv_checker"
	bl_label = "Show UV Checker"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = "Toggle UV Checker. Solid mode only"
	action: bpy.props.BoolProperty(options={'HIDDEN'})

	@classmethod
	def poll(cls, context):
		return context.object is not None and context.object.active_material is not None

	def execute(self, context):
		bpy.context.object.active_material.node_tree.nodes.active.inputs[0].node.show_texture = self.action
		return {'FINISHED'}

class UVRotate(Operator):
	bl_idname = "mesh.rotate_clockwise"
	bl_label = "UV Rotate 90 deg"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = "UV Rotate 90 deg"
	angle : bpy.props.FloatProperty(options = {'HIDDEN'})

	@classmethod
	def poll(cls, context):
		return context.object is not None and context.object.active_material is not None

	def execute(self, context):
		ResetUVSelection(self, context)
		if context.mode == 'OBJECT':
			self.report({'WARNING'},  "UV Rotation can be performed only in Edit Mode!")
		else:
			obj = bpy.context.object
			bm = bmesh.from_edit_mesh(obj.data)
			if bm.select_mode != 'FACE':
				bm.select_mode = {'FACE'}

			sel = [f for f in bm.faces if f.select]

			if bpy.context.scene.tool_settings.use_uv_select_sync == False:
				bpy.context.scene.tool_settings.use_uv_select_sync = True

			bpy.ops.mesh.select_linked(delimit={'UV'})
			if bpy.context.area.type == 'VIEW_3D':
				bpy.context.area.ui_type = 'UV'
				bpy.ops.transform.rotate(value= self.angle, orient_axis='Z', orient_type='VIEW', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='VIEW')
				bpy.ops.uv.select_all(action='DESELECT')
			bpy.context.area.type = 'VIEW_3D'

			for f in sel:
				f.select_set(True)

			bm.select_flush_mode()
			bmesh.update_edit_mesh(obj.data)

		return {'FINISHED'}

class UVMirror(Operator):
	bl_idname = "mesh.uv_miror"
	bl_label = "UV Mirror"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = "UV Mirror"
	axis : bpy.props.BoolVectorProperty(options = {'HIDDEN'})

	@classmethod
	def poll(cls, context):
		return context.object is not None and context.object.active_material is not None

	def execute(self, context):
		if context.mode == 'OBJECT':
			self.report({'WARNING'},  "UV Mirror can be performed only in Edit Mode!")
		else:
			obj = bpy.context.object
			bm = bmesh.from_edit_mesh(obj.data)
			if bm.select_mode != 'FACE':
				bm.select_mode = {'FACE'}

			sel = [f for f in bm.faces if f.select]

			if bpy.context.scene.tool_settings.use_uv_select_sync == False:
				bpy.context.scene.tool_settings.use_uv_select_sync = True
			#bpy.ops.uv.select_all(action='DESELECT')
			bpy.ops.mesh.select_linked(delimit={'UV'})
			if bpy.context.area.type == 'VIEW_3D':
				bpy.context.area.ui_type = 'UV'
				bpy.ops.transform.mirror(orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis= self.axis)
				bpy.ops.uv.select_all(action='DESELECT')
			bpy.context.area.type = 'VIEW_3D'

			for f in sel:
				f.select_set(True)

			bm.select_flush_mode()
			bmesh.update_edit_mesh(obj.data)

		return {'FINISHED'}

class ObjectFixName(Operator):
	bl_label = "Fix Object Name"
	bl_idname = "object.object_fix_name"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = "Fix object names by removing .00# endings"

	@classmethod
	def poll(cls, context):
		return context.object is not None

	def execute(self, context):
		sel = bpy.context.selected_objects

		for i in sel:
			if '.' in i.name:
				removed_rubbish = i.name.split(".", 1)
				i.name = removed_rubbish[0]

		return {'FINISHED'}

class CopyObjectNameToDataName(Operator):
	bl_label = "Copy Object Name To Data Name"
	bl_idname = "object.copy_object_name_to_data_name"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = "Renme Object Data as Object"

	@classmethod
	def poll(cls, context):
		return context.object and context.object.data

	def execute(self, context):
		sel = [obj for obj in bpy.context.selected_objects if obj.type != 'EMPTY']

		for i in sel:
			name = i.data.name
			if i.type == 'MESH' or i.type == 'CURVE':
				pure_name = i.name
				if ' ' in pure_name:
					pure_name = pure_name.replace(' ', '')

				if pure_name is not None and pure_name in bpy.data.meshes:
					i.data = bpy.data.meshes[pure_name]
				else:
					i.data.name = i.name

		return {'FINISHED'}

class FixObjectNameAndAddEndSpaces(bpy.types.Operator):
	bl_idname = "object.name_with_spaces"
	bl_label = "Fix object name"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = "Clean up object name"

	@classmethod
	def poll(cls, context):
		return context.object is not None

	def get_pure_name(self, name):
		if not ' ' and not '.' in name:
			return name

		pure_name = copy.copy(name)

		if ' ' in name:
			pure_name = name.replace(' ', '')

		if '.' in pure_name:	
				pure_name = pure_name.split(".", 1)[0]	

		return pure_name

	def execute(self, context):
		for obj in context.selected_objects:	
			name = self.get_pure_name(obj.name)

			if not name:
				continue	

			if name == obj.name:
				continue

			if name in bpy.data.objects:
				# try to set a name without spaces
				other = bpy.data.objects[name]
				obj.name = find_free_name(self, context, bpy.data.objects, name)
				swap_object_names(self, obj, other)
			else:
				obj.name = name

		return {'FINISHED'}

class FixCollectionNameAndAddEndSpaces(bpy.types.Operator):
	bl_idname = "outliner.name_with_spaces"
	bl_label = "Fix And Name Collection With End Spaces"
	end_char_num: bpy.props.IntProperty(default=4, min=1, max=10)
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = "Fix collection name and keep it the same in Outliner"

	@classmethod
	def poll(cls, context):
		return context.collection is not None

	def execute(self, context):
		collections = bpy.data.collections
		for collection in collections:
			if len(collection.name) <= self.end_char_num:
				continue

			if not '.' in collection.name:
				continue

			name = copy.copy(collection.name[:-self.end_char_num])
			collection.name = find_free_name(self, context, collections, name)

		return {'FINISHED'}

class AutomationRename(bpy.types.Operator):
	bl_idname = "view3d.automation_rename"
	bl_label = "Rename Object"
	bl_description = "If match name found, the new name will contain spaces in the end instead of default Blender .00#"
	bl_options = {'REGISTER', 'UNDO'}
	new_name: bpy.props.StringProperty(options={'HIDDEN'})
	target: bpy.props.EnumProperty(items=[('OBJECT', '', ''), ('COLLECTION', '', '')], options={'HIDDEN'})

	def execute(self, context):
		if self.new_name == '':
			return {'FINISHED'}

		if self.target == 'OBJECT':
			for obj in context.selected_objects:
				name = find_free_name(self, context, bpy.data.objects, self.new_name)
				if obj.name != name:
					obj.name = name

		elif self.target == 'COLLECTION':
			# only context collection
			name = find_free_name(self, context, bpy.data.collections, self.new_name)
			if context.collection.name != name:
				context.collection.name = name

		return {'FINISHED'}

class AutomationRename_CopyName(bpy.types.Operator):
	bl_idname = "view3d.rename_object_copy_name"
	bl_label = ""
	bl_description = "Transfer from Object Name"
	bl_options = {'REGISTER', 'UNDO'}
	target: bpy.props.EnumProperty(items=[('OBJECT', '', ''), ('COLLECTION', '', '')], options={'HIDDEN'})

	# @classmethod
	# def poll(cls, context):
		# return context.object is not None

	def execute(self, context):
		if self.target == 'OBJECT':
			context.scene.new_object_name_input = context.object.name

		elif self.target == 'COLLECTION':
			context.scene.new_collection_name_input = context.collection.name

		return {'FINISHED'}

class ObjectNameRemoveSpaces(Operator):
	bl_label = "Object Name Remove Spaces"
	bl_idname = "object.remove_spaces"
	bl_description = "Object Name Remove Spaces"
	bl_options = {'REGISTER', 'UNDO'}

	def execute(self, context):
		sel = bpy.context.selected_objects

		for i in sel:
			i.name = i.name.replace(' ', '')
		return {'FINISHED'}

class SwapObjectNames(Operator):
	bl_label = "Swap Object Names"
	bl_idname = "object.swap_object_names"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = "Swap names of 2 objects"

	@classmethod
	def poll(cls, context):
		return context.object is not None and len(bpy.context.selected_objects) == 2

	def execute(self, context):
		obj_1, obj_2 = context.selected_objects		
		swap_object_names(self, obj_1, obj_2)
		return {'FINISHED'}

def swap_object_names(cls, obj_1, obj_2):
	if obj_1 is None or obj_2 is None:
		return

	name_1 = copy.copy(obj_1.name)
	name_2 = copy.copy(obj_2.name)
	tmp_name = "tmp_name"

	obj_1.name = "tmp_name"
	obj_2.name = name_1
	obj_1.name = name_2

def fix_mat_names(cls, objects):
	for obj in objects:
		if obj.type == 'MESH' and len(obj.material_slots) > 0:
			mat = obj.active_material
			mat_list = obj.data.materials
			mat_num = len(mat_list) - 1

			for i in mat_list:
				if i != None:
					#select material
					obj.active_material_index = mat_num
					#get material name

					if not obj.active_material:
						continue

					mat_name = obj.active_material.name

					stuff = mat_name.rsplit('.', 1)
					mat_name = stuff[0]

					#assign material
					if mat_name in bpy.data.materials:
						obj.data.materials[mat_num] = bpy.data.materials[mat_name]
					else:
						obj.data.materials[mat_num].name = mat_name

					mat_num -= 1

class FixMaterialName(Operator):
	bl_idname = "object.fix_material_name"
	bl_label = "Fix Material Name"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = "Fix material names by removing .00# endings"	

	def execute(self, context):			
		fix_mat_names(self, bpy.context.selected_objects)

		return {'FINISHED'}

class ReplaceMaterials(Operator):
	bl_idname = "object.replace_materials"
	bl_label = "Replace Materials"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = "Replace Materials"

	@classmethod
	def poll(cls, context):
		return context.object is not None and len(bpy.context.object.material_slots) > 0

	def do_replace(self, context, obj):
		src	= bpy.context.scene.src_mat
		trg	= bpy.context.scene.trg_mat

		index = 0
		if obj and obj.type == 'MESH' and len(obj.material_slots) > 0:
			mat_list = obj.data.materials[:]
			for i in mat_list:
				#replace
				if i.name == trg:
					if src in bpy.data.materials:
						obj.data.materials[index] = bpy.data.materials[src]
					else:
						obj.data.materials[index].name = src
						#break
				index += 1


	def execute(self, context):
		sel = bpy.context.selected_objects
		if sel:
			for obj in sel:
				bpy.context.view_layer.objects.active = obj
				self.do_replace(context, obj)
		else:
			self.do_replace(context, bpy.context.object)

		return {'FINISHED'}

class ReplaceMaterialsGetter(Operator):
	bl_idname = "object.replace_materials_get_material"
	bl_label = "Replace Materials Get/Set Buttons"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = "Get Material name from Material Slot"
	mat : bpy.props.StringProperty(options={'HIDDEN'})

	@classmethod
	def poll(cls, context):
		return context.object is not None and len(bpy.context.object.material_slots) > 0

	def execute(self, context):
		active_material = bpy.context.active_object.active_material.name
		if self.mat== 'src':
			bpy.context.scene.src_mat = active_material
		elif self.mat== 'trg':
			bpy.context.scene.trg_mat = active_material

		return {'FINISHED'}

class ReplaceMaterialsAdder(Operator):
	bl_idname = "object.replace_materials_add_material"
	bl_label = "Replace Materials Add Buttons"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = "Add a new or existing material to the material slot. A new one will be added if the material specified in target/source fields does not exist"
	mat : bpy.props.StringProperty(options={'HIDDEN'})

	@classmethod
	def poll(cls, context):
		return context.object is not None and len(bpy.context.object.material_slots) > 0

	def execute(self, context):
		sel = bpy.context.selected_objects
		data = bpy.data
		src	= bpy.context.scene.src_mat
		trg	= bpy.context.scene.trg_mat
		for obj in sel:
			if self.mat== 'add_src':
				if src not in data.materials:
					new_mat = data.materials.new(src)
					obj.data.materials.append(new_mat)
				else:
					obj.data.materials.append(data.materials[src])

			elif self.mat== 'add_trg':
				if trg not in data.materials:
					new_mat = data.materials.new(trg)
					obj.data.materials.append(new_mat)
				else:
					obj.data.materials.append(data.materials[trg])
		obj.active_material_index = len(obj.data.materials) -1


		return {'FINISHED'}

class AddBodyMaterials(Operator):
	bl_label = "Generate Body Materials"
	bl_idname = "object.add_body_materials"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = "Generate Body Materials"

	@classmethod
	def poll(cls, context):
		return context.object is not None

	def execute(self, context):
		# materials list
		mat_list = [
		'Paint',
		'Bonnet',
		'Bumper_Front',
		'Bumper_Rear',
		'Chrome',
		'Paint_Two_Tone',
		'Plastic',
		'Car_Roof',
		'Trim',
		'Window_Pillar',
		'Window_Trim',
		'Windows',
		'BonnetCam',
		'DriverCam',
		'LipPlacement',
		'Miscellaneous'
		]

		# add to the mesh material slots
		for i in range (len(mat_list)):
			mat = bpy.data.materials.new(name = mat_list[i])
			bpy.context.object.data.materials.append(mat)
			mat.diffuse_color = (uniform(0.0, 0.7), uniform(0.0, 0.7), uniform(0.0, 0.7), 1)

		return {'FINISHED'}

class AddFixtureMaterials(Operator):
	bl_label = "Generate Fixture Materials"
	bl_idname = "object.add_fixture_materials"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = "Generate Fixture Materials"

	@classmethod
	def poll(cls, context):
		return context.object is not None

	def execute(self, context):
		# materials list
		mat_list = [
		'Reflector',
		'Glass',
		'Panel',
		'Bolt'
		]

		# add to the mesh material slots
		for i in range (len(mat_list)):
			mat = bpy.data.materials.new(name = mat_list[i])
			bpy.context.object.data.materials.append(mat)
			mat.diffuse_color = (uniform(0.0, 0.7), uniform(0.0, 0.7), uniform(0.0, 0.7), 1)

		return {'FINISHED'}

class ClearMatSlots(Operator):
	bl_label = "Delete All Mesh Materials"
	bl_idname = "object.delete_all_mesh_mats"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = "Delete All Mesh Materials"

	@classmethod
	def poll(cls, context):
		return context.object is not None

	def execute(self, context):
		sel = []
		sel = bpy.context.selected_objects
		if len(sel) < 1:
			sel.append(bpy.context.object)

		for o in sel:
			if o.type == "MESH" or "CURVE":
				o.select_set(True)
				bpy.context.view_layer.objects.active = o

				if bpy.context.active_object and len(bpy.context.active_object.material_slots) > 0:
					current_mode = bpy.context.mode
					if current_mode == 'EDIT_MESH':
						bpy.ops.object.mode_set(mode = 'OBJECT')
					for i in bpy.context.active_object.data.materials:
						bpy.ops.object.material_slot_remove()
					if current_mode == 'EDIT_MESH':
						bpy.ops.object.mode_set(mode = 'EDIT')

		bpy.ops.object.select_all(action='DESELECT')
		for obj in sel:
			obj.select_set(True)

		return {'FINISHED'}

class CleanUpUnusedMatsMesh(Operator):
	bl_label = "Delete unused Mesh Materials"
	bl_idname = "object.cleanup_unused_mesh_mats"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = "Delete unused Mesh Materials"

	@classmethod
	def poll(cls, context):
		return context.object is not None

	def execute(self, context):
		sel = []
		sel = bpy.context.selected_objects
		if len(sel) < 1:
			sel.append(bpy.context.object)

		# switch to object mode
		if_object_mode = False
		if bpy.context.active_object:
			if bpy.context.object.type == "MESH":
				if bpy.context.mode == "EDIT_MESH":
					bpy.ops.object.mode_set(mode = 'OBJECT')
					if_object_mode = True
		if len(sel):
			for o in sel:
				if len(o.material_slots) > 0:
					o.select_set(True)
					bpy.context.view_layer.objects.active = o

					# initial number of slots
					old_slots_mumber = len(o.material_slots)

					bpy.ops.object.material_slot_remove_unused()

					if if_object_mode:
						bpy.ops.object.mode_set(mode = 'EDIT')

					# new number of slots
					new_slots_mumber = len(o.material_slots)

					# how many unused slots were removed?
					difference = old_slots_mumber - new_slots_mumber

					if difference > 0:
						self.report({'INFO'}, o.name + ": " + str(difference) + " slots removed")
		else:
			self.report({'WARNING'},  "Nothing selected!")

		bpy.ops.object.select_all(action='DESELECT')
		for obj in sel:
			obj.select_set(True)
		return {'FINISHED'}


class RemoveDuplicates(Operator):
	bl_label = "Remove Duplicated Items"
	bl_idname = "view3d.remove_duplicated_items"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = "Remove Duplicated items from their collections"

	collection: bpy.props.IntProperty(options={'HIDDEN'})

	def remap_and_remove(self, collection):
		# remove duplicates
		for item in collection:
			if  not item.name[::-1][:3].isnumeric():
				# here we have a pure object and can now start looking for its copies
				for copy in collection:
					if copy is not item and item.name == copy.name.rsplit(copy.name[-4])[0] and copy.name[::-1][:3].isnumeric():
						#now remap to the hopefully original data block and delete
						copy.user_remap(item)
						collection.remove(copy, do_unlink=True)
		#try to clean up names by removing automatically generated numeric endings
		for item in collection:
			if len(item.name) > 4:
				if item.name[::-1][:3].isnumeric():
					item.name = item.name.rsplit(item.name[-4])[0]


	def execute(self, context):
		match self.collection:
			case 0:
				self.remap_and_remove(bpy.data.materials)
			case 1:
				self.remap_and_remove(bpy.data.images)
			case 2:
				self.remap_and_remove(bpy.data.meshes) 
			case default:
				self.remap_and_remove(bpy.data.materials)
				self.remap_and_remove(bpy.data.images)

		return {'FINISHED'}

class CleanUpMatsScene(Operator):
	bl_label = "Delete unused Scene Materials"
	bl_idname = "object.cleanup_mats_scene_unused"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = "Delete unused Scene Materials"

	@classmethod
	def poll(cls, context):
		return len(bpy.data.materials) > 0

	def execute(self, context):
		rubbish_data = [m for m in bpy.data.materials if m.users == 0]
		counter = 0
		mat = ""
		for i in rubbish_data:
			mat = ""
			bpy.data.materials.remove(i)
			if mat not in bpy.data.materials:
				counter += 1
		self.report({'INFO'},  (str(counter) + " unused Scene Materials have been deleted"))

		return {'FINISHED'}

class CleanUpMatsSceneAll(Operator):
	bl_label = "Delete All Scene Materials"
	bl_idname = "object.cleanup_mats_scene_all"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = "Delete All Scene Materials"

	@classmethod
	def poll(cls, context):
		return len(bpy.data.materials) > 0

	def execute(self, context):
		# delete all scene materials
		rubbish_data = [m for m in bpy.data.materials]

		for i in rubbish_data:
			bpy.data.materials.remove(i)

		# delete all objects materials
		for o in bpy.data.objects:
			if o.type == "MESH" or o.type == "CURVE":
				if o.hide_select == False and o.hide_viewport == False:
					if o.name in  bpy.context.view_layer:
						o.select_set(True)
						bpy.context.view_layer.objects.active = o
						ops.delete_all_mesh_mats()
		bpy.ops.object.select_all(action='DESELECT')

		if len(bpy.data.materials) == 0:
			self.report({'INFO'},  "All Scene Materials have been deleted")

		return {'FINISHED'}

class ResetNormalsObject(Operator):
	bl_label = "Reset Normals Object"
	bl_idname = "object.reset_normals_object"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = 'Reset mesh normals to fix shading issues'

	@classmethod
	def poll(cls, context):
		return context.active_object is not None and context.object.type == "MESH"

	def execute(self, context):
		mode = context.mode
			
		if mode != 'EDIT_MESH':
			 bpy.ops.object.mode_set(mode = 'EDIT')	

		if mode == 'EDIT_MESH':
			mode = 'EDIT'
		
		mesh = context.object.data			
		bm = bmesh.from_edit_mesh(mesh)

		verts = [v for v in bm.verts if v.select]
		edges = [e for e in bm.edges if e.select]		
		faces = [f for f in bm.faces if f.select]			

		bpy.ops.mesh.select_all(action='SELECT')
		bpy.ops.mesh.normals_tools(mode="RESET")
		bpy.ops.mesh.select_all(action='DESELECT')

		# for v in verts:
		# 	v.select_set(True)

		# for e in edges:
		# 	e.select_set(True)

		# for f in faces:
		# 	f.select_set(True)

		bpy.ops.object.mode_set(mode = mode)

		return {'FINISHED'}

class ToggleZeroOneValuesActiveShapeKey(Operator):
	bl_label = ""
	bl_idname = "object.toggle_0_1_active_shape_key"
	bl_description = 'Toggle between 0 and 1'
	value: bpy.props.FloatProperty(min = 0.0, max = 1.0, options = {'HIDDEN'})

	@classmethod
	def poll(cls, context):
		return context.object

	def execute(self, context):
		obj = context.object
		obj.active_shape_key.value = self.value
		return {'FINISHED'}

class ToggleZeroOneValuesVertexWeight(Operator):
	bl_label = ""
	bl_idname = "object.toggle_0_1_vertex_weight"
	bl_description = 'Toggle between 0 and 1'
	value: bpy.props.FloatProperty(min = 0.0, max = 1.0, options = {'HIDDEN'})

	@classmethod
	def poll(cls, context):
		return context.object

	def execute(self, context):
		bpy.context.scene.tool_settings.vertex_group_weight = self.value
		return {'FINISHED'}

class AddEmptyShapeKeys(Operator):
	bl_label = 'Add Empty Rim Shape Keys'
	bl_idname = 'object.add_empty_shape_keys'
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = "Add empty Body/Rim shape keys. Body shape key generator takes an active vertex group's name to name a new key. Rim gets 3 empty keys: Base, Scale, Offset"
	type: bpy.props.StringProperty(options = {'HIDDEN'})
	@classmethod
	def poll(cls, context):
		return context.object

	def execute(self, context):
		obj = context.object
		if self.type == 'RIM':
			keys = ('Basis', 'Scale','Offset')
			for key in keys:
				if obj.data.shape_keys is not None and key not in obj.data.shape_keys.key_blocks or obj.data.shape_keys is None:
					bpy.ops.object.shape_key_add(from_mix=False)
					obj.active_shape_key.name = key
				else:
					self.report({'WARNING'}, 'The Rim shape keys are already in the stack!')
					break
		elif self.type == 'BODY':
			if len(obj.vertex_groups):
				vg = obj.vertex_groups.active.name
				bpy.ops.object.shape_key_add(from_mix=False)
				obj.active_shape_key.name = vg

		return {'FINISHED'}

class ToggleCarPaint(Operator):
	bl_label = "Check Reflections"
	bl_idname = "view3d.toggle_carpaint"
	bl_description = "Toggle between Car Paint and Basic Viewport Shading. Requires Active Mesh selection"

	@classmethod
	def poll(cls, context):
		return _class_method_mesh_(cls, context)

	def execute(self, context):

		wp_mode = bpy.context.scene.weight_paint_mode

		if bpy.context.space_data.shading.type != 'SOLID':
					bpy.context.space_data.shading.type = 'SOLID'

		if bpy.context.space_data.shading.light == 'MATCAP':
			if bpy.context.space_data.shading.studio_light == 'metal_carpaint.exr':
				# check weight_paint_mode
				if wp_mode:
					bpy.ops.object.weight_paint_mode_on()
					bpy.context.space_data.shading.studio_light = 'basic_1.exr'
				else:
					bpy.context.space_data.shading.studio_light = 'basic_1.exr'

			else:
				bpy.context.space_data.shading.studio_light = 'metal_carpaint.exr'

				# if called from weight paint mode
				if bpy.context.mode == 'PAINT_WEIGHT':
					bpy.ops.object.object_edit_mode_on(mode='OBJECT')
					bpy.context.scene.weight_paint_mode = True
				else:
					bpy.context.scene.weight_paint_mode = False

		# if not matcap
		else:
			bpy.context.space_data.shading.light = 'MATCAP'
			bpy.context.space_data.shading.studio_light = 'metal_carpaint.exr'
			if bpy.context.mode == 'PAINT_WEIGHT':
				bpy.ops.object.object_edit_mode_on(mode='OBJECT')

		return {'FINISHED'}

class FillVertexColors(Operator):
	bl_idname = "mesh.fill_vertex_colors"
	bl_label = "Fill vertices"
	bl_description = "Fill vertex color"
	bl_options = {'REGISTER', 'UNDO'}
	color: bpy.props.FloatVectorProperty(name='Color', subtype='COLOR', size=4, min=0.0, max=1.0, default=(0, 0, 0, 1))

	@classmethod
	def poll(cls, context):
		return context.object

	def execute(self, context):
		# update_object_edit(context)
		if context.mode != 'OBJECT':
			bpy.ops.object.mode_set(mode='OBJECT')
		
		for obj in [obj for obj in context.selected_objects if obj.type == 'MESH']:
			mesh = obj.data			
			active = mesh.attributes.active_color
			if active is not None and active.name != 'Color':
				active.name = 'Color'				
				update_edit_object(context)

			bm = bmesh.new()
			bm.from_mesh(mesh)
		
			color = bm.loops.layers.color.get('Color')				

			if color is None:		
				if 'Color' not in mesh.attributes:
					color = bm.loops.layers.color.new('Color')
					bm.to_mesh(mesh)					
					mesh.attributes.active_color = mesh.attributes["Color"]
				else:		
					self.report({'WARNING'}, obj.name + ': ' + "Color Attribute \'Color\' already exists. Note that it has to be a single color CORNER & BYTE_COLOR attribute and named \'Color\'")
					continue

			# fill polygons
			if mesh.use_paint_mask:
				bm.faces.ensure_lookup_table()
				faces = [face for face in bm.faces if face.select]

				for face in faces if len(faces)>0 else bm.faces:
					for loop in face.loops:
						loop[color] = self.color
			# fill verts
			else:
				bm.verts.ensure_lookup_table()
				verts = [vert for vert in bm.verts if vert.select]
				for vert in verts if len(verts)>0 else bm.verts:
					for loop in vert.link_loops:
						loop[color] = self.color

			bm.to_mesh(mesh)		
			bm.free()
		update_edit_object(context)
		bpy.ops.object.mode_set(mode = 'EDIT')

		return {'FINISHED'}

class InvertVertexColors(Operator):
	bl_idname = "object.invert_vertex_colors"
	bl_label = "Invert RGB values"
	bl_description = "Invert RGB values"
	bl_options = {'REGISTER', 'UNDO'}

	@classmethod
	def poll(cls, context):
		return context.object is not None and context.object.type == 'MESH'

	def execute(self, context):
		if context.mode != 'OBJECT':			
			bpy.ops.object.mode_set(mode='OBJECT')

		for obj in [obj for obj in context.selected_objects if obj.type == 'MESH']:
			mesh = obj.data
			bm = bmesh.new()
			bm.from_mesh(mesh)

			color = bm.loops.layers.color.get('Color')
			if color is None:	
				if 'Color' not in mesh.attributes:
					color = bm.loops.layers.color.new('Color')
					bm.to_mesh(mesh)					
					mesh.attributes.active_color = mesh.attributes["Color"]					
				else:		
					self.report({'WARNING'}, obj.name + ': ' + "Color Attribute \'Color\' already exists. But it should be converted to CORNER and BYTE_COLOR to be seen by BMesh")
					continue

			for face in bm.faces:
				for loop in face.loops:
					loop[color][0] = 1.0 - loop[color][0]
					loop[color][1] = 1.0 - loop[color][1]
					loop[color][2] = 1.0 - loop[color][2]
			
			bm.to_mesh(mesh)
			bm.free()
		update_edit_object(context)

		return {'FINISHED'}

class ConvertAOtoExhaustHeatMap(Operator):
	bl_idname = "object.ao_to_exhaust_heatmap"
	bl_label = "AO to Exhaust"
	bl_description = "Convert AO to Exhaust Vertex Colors"
	bl_options = {'REGISTER', 'UNDO'}
	value: bpy.props.FloatProperty(min=0.0, max=1.0, default=0.2)
	use_heat_source: bpy.props.BoolProperty()
	blur: bpy.props.BoolProperty()

	@classmethod
	def poll(cls, context):
		return context.object is not None

	def draw(self, context):
		layout = self.layout
		column = layout.column(align=True)
		column.prop(self, 'value', text='Value')
		column.separator()
		column.prop(self, 'use_heat_source', text='Use Heat Points')	
		column.separator()
		column.prop(self, 'blur', text='Blur')

	def calculate_average(self, verts):
		if not len(verts) > 0:
			return Vector()
		total = sum(verts,  Vector().to_4d())
		return total * (1/len(verts))

	def execute(self, context):
		obj = context.object
		mesh = context.object.data

		bm = bmesh.new()
		bm.from_mesh(mesh)
		bm.verts.ensure_lookup_table()
		bm.faces.ensure_lookup_table()
		
		if context.mode != 'OBJECT':		
			bpy.ops.object.mode_set(mode='OBJECT')

		mesh = context.object.data	
		active_color = mesh.attributes.active_color
		
		if active_color == None:
			self.report({'WARNING'}, "Active Color Attribute not found!")	
			active_color = 	mesh.attributes.active_color	

		if active_color.domain != 'POINT':
			bpy.ops.geometry.color_attribute_convert(domain='POINT', data_type='BYTE_COLOR')
			self.report({'WARNING'}, "Color Attribute converted to CORNER and BYTE_COLOR!")

		active_color = mesh.attributes.active_color
	
		# each empty heat point will work as a light source to intensify heat value at pipe bends 
		heat_multiplier_intensity = 0.0005
		heat_multiplier_size = 0.0001
		heat_multiplier_positions = [hm.location for hm in context.view_layer.objects if ('HeatMultiplier' in hm.name and not hm.hide_render)]
		glow_intensity = 1.0

		# box blur
		if self.blur:
			for vert in bm.verts:
				linked_verts_colors = []
				for face in vert.link_faces:
					for v in face.verts:
						if v is not vert:
							linked_verts_colors.append(Vector(active_color.data.items()[v.index][1].color[:]))

				active_color.data.items()[vert.index][1].color[:] = self.calculate_average(linked_verts_colors)

		# glowing
		for vert in bm.verts:					
			color_data = active_color.data.items()[vert.index][1]
			
			#https://seblagarde.wordpress.com/wp-content/uploads/2015/07/course_notes_moving_frostbite_to_pbr_v32.pdf
			if self.use_heat_source:
				glow_intensity = 0.0
				for pos in heat_multiplier_positions:
					distance_from_hm = (obj.matrix_world@vert.co - pos).length
					glow_intensity += heat_multiplier_intensity/(max(pow(distance_from_hm, 2), pow(heat_multiplier_size, 2)))
			else:
				glow_intensity = 1.0	

			# we'll save source AO values in alpha channel, which then can be used as a mask where it is needed
			color_data.color = (((1.0 - color_data.color[0])*self.value)*glow_intensity if not vert.is_boundary else 0.0, 0.0, 0.0, color_data.color[0] if not vert.is_boundary else 0.0)			
		
		bm.free()	
		return {'FINISHED'}

class ChangeVertexColorBrightness(Operator):
	bl_idname = "mesh.change_vertex_color_brightness"
	bl_label = "Brightness"
	bl_description = "Edit Brightness of each RGBA channel"
	bl_options = {'REGISTER', 'UNDO'}
	multiplier: bpy.props.FloatVectorProperty(name='RGBA Channels', min=0.0, max=10.0, size=4, default=(1.0,1.0,1.0,1.0), options={'SKIP_SAVE'})

	@classmethod
	def poll(cls, context):
		return context.object is not None

	def execute(self, context):
		if context.mode != 'OBJECT':
			bpy.ops.object.mode_set(mode = 'OBJECT')

		update_edit_object(context)

		for obj in [obj for obj in context.selected_objects if obj.type == 'MESH']:
			mesh = obj.data
			bm = bmesh.new()
			bm.from_mesh(mesh)

			color = bm.loops.layers.color.get('Color')
			if color is None:		
				if 'Color' not in mesh.attributes:
					color = bm.loops.layers.color.new('Color')
					bm.to_mesh(mesh)					
					mesh.attributes.active_color = mesh.attributes["Color"]					
				else:
					bpy.ops.geometry.color_attribute_convert(domain='CORNER', data_type='BYTE_COLOR')
					self.report({'WARNING'}, obj.name + ': ' + "Color Attribute \'Color\' already exists. It has been converted to CORNER and BYTE_COLOR to be seen by BMesh and needs reatsrt. Call the command again to have it worked")

					continue

			color = bm.loops.layers.color.get('Color')
			if color is None:
				self.report({'WARNING'}, obj.name + ': ' + "Color Attribute \'Color\' not found!'")
				return {'CANCELLED'}

			verts = [vert for vert in bm.verts if vert.select]	

			for vert in verts if len(verts)>0 else bm.verts:
				for loop in vert.link_loops:
					loop[color] = Vector((
											loop[color][0]*self.multiplier[0],
											loop[color][1]*self.multiplier[1],
											loop[color][2]*self.multiplier[2],
											loop[color][3]*self.multiplier[3]
											))
			
			bm.to_mesh(mesh)
			bm.free()
			
		bpy.ops.object.mode_set(mode = 'EDIT')		

		return {'FINISHED'}

class GenerateIDColors(Operator):
	bl_idname = "object.generate_id_colors"
	bl_label = "Generate random ID colors"
	bl_description = "Generate random ID colors. Supports only 'Principled BSDF' based materials"
	bl_options = {'REGISTER', 'UNDO'}

	@classmethod
	def poll(cls, context):
		return context.object is not None

	def apply_random_color(self, context, mat):
		color = Color((uniform(0,1), uniform(0,1), uniform(0,1)))
		try:
			mat.node_tree.nodes["Principled BSDF"].inputs[0].default_value = (color[0], color[1], color[2], 1)
			mat.diffuse_color = (color[0], color[1], color[2], 1)
		except:
			self.report({'WARNING'}, mat.name + ": Could not change Base Color! Make sure that the material uses 'Principled BSDF'")

	def execute(self, context):
		data = bpy.data
		for obj in context.selected_objects:
			mats = obj.data.materials
			if len(mats) == False:
				template = "IDMaterial_"
				mat = None
				existing_id_mats = [m.name for m in data.materials if template in m.name]
				if len(obj.data.materials) == False and len(existing_id_mats):
					existing_id_mats.sort()
					mat_number = int(existing_id_mats[-1].rsplit('_', 1)[1])
					mat = data.materials.new(name = template+str(mat_number + 1))
					mat.use_nodes = True
				elif len(obj.data.materials) == False and len(existing_id_mats) == False:
					mat = data.materials.new(name="IDMaterial_1")
				obj.data.materials.append(mat)
				self.apply_random_color(context, mat)
			else:
				for mat in mats:
					if mat.use_nodes == False:
						mat.use_nodes = True
					self.apply_random_color(context, mat)
		return {'FINISHED'}

class CopyObjectName(Operator):
	bl_idname = "object.copy_object_name"
	bl_label = "Copy Object Name"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = "Copy Object Name"

	@classmethod
	def poll(cls, context):
		return context.object is not None

	def execute(self, context):
		obj = bpy.context.object
		if obj is not None:
			bpy.context.window_manager.clipboard = obj.name
		else:
			self.report({'WARNING'},  "Source object not found!")

		return {'FINISHED'}

class PasteObjectName(Operator):
	bl_idname = "object.paste_object_name"
	bl_label = "Paste Object Name"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = "Paste Object Name"

	@classmethod
	def poll(cls, context):
		return context.object is not None

	def execute(self, context):
		sel = bpy.context.selected_objects
		if len(sel):
			for i in sel:
				i.name = find_free_name(self, context, bpy.data.objects, bpy.context.window_manager.clipboard)

		return {'FINISHED'}

class NameForBake(Operator):
	# select 2 meshes and call the command. Highest will get suffix/name "_high", lowest "_low"
	bl_idname = "object.rename_lp_hp"
	bl_label = "Name For Bake"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = "Add *_lp and *_hp in the ends of high/low poly meshes. Select 2 meshes and run the script"

	@classmethod
	def poll(cls, context):
		return context.active_object is not None

	def execute(self, context):

		sel = bpy.context.selected_objects
		if len(sel) == 2:
			if sel[0].type == 'MESH' and sel[1].type == 'MESH':
				if len(sel[0].data.vertices) > len(sel[1].data.vertices):
					sel[1].name = sel[0].name + "_low"
					sel[0].name = sel[0].name + "_high"
				else:
					sel[1].name = sel[0].name + "_high"
					sel[0].name = sel[0].name + "_low"

		return {'FINISHED'}

class CreateGroup(Operator):
	#all LODs must be properly named before use
	bl_idname = "object.create_group"
	bl_label = "Create Group"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = "Add a new Group(Empty) and parent selected objects inside"

	@classmethod
	def poll(cls, context):
		return context.object is not None

	def execute(self, context):
		sel = bpy.context.selected_objects
		ao = bpy.context.active_object
		bpy.ops.object.select_all(action='DESELECT')

		# if empty in the selection list, deselect it
		for i in sel:
			if i.type != "EMPTY":
				i.select_set(True)
		sel = bpy.context.selected_objects
		bpy.context.view_layer.objects.active = ao

		# if the objects have a parent
		parent_empty = bpy.context.active_object.parent

		if len(sel):
			# get collection
			col = sel[0].users_collection[0].name
			 # if not Scene Collection
			bpy.ops.collection.objects_add_active(collection = col)

			#add empty
			bpy.ops.object.empty_add(type='PLAIN_AXES', radius=0.00001, location = (0,0,0))
			new_empty = bpy.context.active_object

			# parent if parent exists
			if parent_empty is not None:
				new_empty.parent = parent_empty

			#parenting
			for i in sel:
				i.parent = new_empty

			new_empty.name = sel[0].name
			sel[0].select_set(True)
			bpy.ops.object.swap_object_names()

		return {'FINISHED'}

class CreateCollection(Operator):
	#all LODs must be properly named before use
	bl_idname = "object.create_collection_with_objects"
	bl_label = "Create Collection"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = "Add a new Collection and parent selected objects inside"

	@classmethod
	def poll(cls, context):
		return context.object is not None

	def find_collection(self, ao):
		#find the active object's parent collection
		collections = bpy.data.collections
		if len(collections) > 0:
			for collection in collections:
				if len(collection.objects) > 0:
					if ao.name in collection.objects:
						return collection
					else:
						continue
		else:
			return bpy.context.view_layer.active_layer_collection.collection

	def execute(self, context):
		sel = bpy.context.selected_objects
		ao = bpy.context.active_object

		parent_collection = self.find_collection(ao)

		new_collection = bpy.context.blend_data.collections.new(name= ao.name)

		if parent_collection is not None:
			parent_collection.children.link(new_collection)
			for obj in sel:
				new_collection.objects.link(obj)
				parent_collection.objects.unlink(obj)
		else:
			parent_collection = bpy.context.view_layer.active_layer_collection.collection
			parent_collection.children.link(new_collection)
			for obj in sel:
				new_collection.objects.link(obj)
				parent_collection.objects.unlink(obj)

		return {'FINISHED'}

class MoveToSceneCenter(Operator):
	bl_idname = "object.move_to_scene_center"
	bl_label = "Move to Center"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = "Move to Center"

	@classmethod
	def poll(cls, context):
		return context.object is not None

	def execute(self, context):
		sel = bpy.context.selected_objects
		if len(sel):
			for i in sel:
				i.location = (0.0, 0.0, 0.0)
				# if i.parent:
					# self.report({'WARNING'},  "Nothing changed. Select the top parent and try again")
					# return {'FINISHED'}

				# if i.type != 'EMPTY' and i.data.users > 1:
					# self.report({'WARNING'},  "Nothing changed. The mesh has instances")
					# return {'FINISHED'}
				# else:
					# i.location = (0.0, 0.0, 0.0)

		return {'FINISHED'}

class TransferTransform(Operator):
	bl_idname = "object.transfer_transform"
	bl_label = "Transfer Transform"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = "Transfer Transform"
	location: bpy.props.BoolProperty(name='Location', default=True)
	rotation: bpy.props.BoolProperty(name='Rotation', default=True)
	scale: bpy.props.BoolProperty(name='Scale', default=True)
	replace: bpy.props.BoolProperty(name='Replace original', default=False)

	@classmethod
	def poll(cls, context):
		return context.object is not None

	def execute(self, context):
		ao = bpy.context.active_object
		ao.rotation_mode = 'QUATERNION'
		if ao != None:
			sel = [o for o in bpy.context.selected_objects if o!= ao]
			if	len(sel):
				for i in sel:
					if self.location:
						i.location = ao.location
					if self.rotation:
						i.rotation_mode = 'QUATERNION'				
						i.rotation_quaternion = ao.rotation_quaternion
					if self.scale:
						i.scale = ao.scale

		if self.replace:
			context.view_layer.objects.active = sel[0]
			bpy.data.objects.remove(ao, do_unlink=True)
		return {'FINISHED'}

class AddEmptyInComponentSelectionCenter(Operator):
	bl_idname = "object.add_empty_in_gizmo"
	bl_label = "Add Empty in Selection Center"
	bl_description = "Add an empty positioned inside the center of selected mesh/curve components"
	bl_options = {'REGISTER', 'UNDO'}	
	empty_name: bpy.props.StringProperty(name='Name', default='Empty')
	size: bpy.props.FloatProperty(default=0.01, name='Size')
	scale: bpy.props.FloatVectorProperty(name='Scale', default=(1,1,1))#, default=(0.01, 0.01, 0.01)
	align: bpy.props.BoolProperty(name='Align', default=False)	
	empty_display_type: bpy.props.EnumProperty(name='Display',
	 items=[
		 ('PLAIN_AXES', 'PLAIN_AXES', '', 0),		
		 ('ARROWS', 'ARROWS', '', 1),
		 ('SINGLE_ARROW', 'SINGLE_ARROW', '', 2),
		 ('CIRCLE', 'CIRCLE', '', 3),
		 ('CUBE', 'CUBE', '', 4),		
		 ('SPHERE', 'SPHERE', '', 5),
		 ('CONE', 'CONE', '', 6),
		 ('IMAGE', 'IMAGE', '', 7),
		 ],	 
		  default='PLAIN_AXES')
	forward_axis: bpy.props.EnumProperty(items=[
		('X', 'X', '', 0),
		('Y', 'Y', '', 1),
		('Z', 'Z', '', 2),
		('-X', '-X', '', 3),
		('-Y', '-Y', '', 4),
		('-Z', '-Z', '', 5)
		],
		name='Forward', default='Z' )
	up_axis: bpy.props.EnumProperty(items=[
		('X', 'X', '', 0),
		('Y', 'Y', '', 1),
		('Z', 'Z', '', 2)],
		name='Up', default='X')
	
	@classmethod
	def poll(cls, context):
		obj = context.object
		return obj is not None and (obj.type == 'MESH' or obj.type == 'CURVE')

	def draw(self, context):
		layout = self.layout
		column = layout.column()		
			
		column.prop(self, 'empty_name')
		column.prop(self, 'empty_display_type')
		row = layout.row()
		row.label(text='Size:')
		row.prop(self, 'size', text = '')
		row = layout.row()
		row.label(text='Scale:')			
		row.prop(self, 'scale', text = '')
		column = layout.column()
		column.prop(self, 'align')
		if self.align:
			column.prop(self, 'forward_axis')
			column.prop(self, 'up_axis')

	def find_median_position(self, verts):
		if not len(verts) > 0:
			return Vector()
		pos_sum = Vector()
		for vert in verts:
			pos_sum = pos_sum + vert		
		return pos_sum * (1/len(verts))

	def spawn_empty(self, context):
		empty = bpy.data.objects.new(self.empty_name, None)
		empty.empty_display_size = self.size
		empty.empty_display_type = self.empty_display_type
		return empty

	def spawn(self, context, verts):
		obj = context.object
		scene = context.scene

		new_obj = None
		scale = self.scale
		new_obj = self.spawn_empty(context)			

		if new_obj is None:
			return

		# link new object to the scene
		context.layer_collection.collection.objects.link(new_obj)	

		# align to the source mesh component selection
		if self.align and not len(verts) > 2:			
			self.report({'WARNING'}, self.bl_idname + ': '  + 'Not enough points to calculate rotation. Should be at least 3')		

		if self.align and obj.type == 'MESH' and len(verts) > 2:
			# calculate normal
			v1 = verts[0] - verts[1]
			v2 = verts[1] - verts[2]
			cross = v1.cross(v2).normalized()

			# calculate rotation
			if self.forward_axis == self.up_axis:
				self.report({'WARNING'}, self.bl_idname + ': '  + 'Forward and Up can\'t be the same axis')	
				self.forward_axis = 'Z'
				self.up_axis = 'X'

			rotation = cross.to_track_quat(self.forward_axis, self.up_axis)

			new_obj.rotation_mode = 'QUATERNION'
			matrix = obj.matrix_world
			new_obj.matrix_world = obj.matrix_world @ Matrix.LocRotScale(
				self.find_median_position(verts),
				rotation,
				scale)
		else:
			new_obj.matrix_world = obj.matrix_world @ Matrix.LocRotScale(
				self.find_median_position(verts),
				Quaternion(),
				scale)

	def execute(self, context):
		obj = context.object
		verts = []

		# update selection
		bpy.ops.object.mode_set(mode = 'OBJECT')
		bpy.ops.object.mode_set(mode = 'EDIT')

		# if context object is mesh
		if obj.type == 'MESH':
			bm = bmesh.new()
			bm.from_mesh(obj.data)
			bm.verts.ensure_lookup_table()	
			verts = [v.co for v in bm.verts if v.select]
			bm.free()

		# if context object is curve		
		elif obj.type == 'CURVE':
			for spline in obj.data.splines:
				if spline.type == 'POLY' or spline.type == 'NURBS':
					for point in spline.points:
						if point.select:
							verts.append(Vector((point.co[:3])))
				elif spline.type == 'BEZIER':
					for point in spline.bezier_points:
						if point.select_control_point:
							verts.append(Vector((point.co)))
						if point.select_left_handle:
							verts.append(Vector((point.handle_left)))
						if point.select_right_handle:
							verts.append(Vector((point.handle_right)))

		if len(verts) > 0:
			self.spawn(context, verts)
		else:
			self.report({'ERROR'}, self.bl_idname + ": " + "No verts/points selected!")

		return {'FINISHED'}

class AddEmptyInLoop(Operator):
	bl_idname = "object.empty_in_loop"
	bl_label = "Empty in Mesh Loop"
	bl_description = "Create empties in the centers of selected mesh loops"
	bl_options = {'REGISTER', 'UNDO'}
	name: bpy.props.StringProperty(name='Name')
	scale: bpy.props.FloatVectorProperty(name='Scale', default=(0.01, 0.01, 0.01))
	radius: bpy.props.FloatProperty(default=0.01, name='Radius')
	align: bpy.props.BoolProperty(name='Align')
	empty_display_type: bpy.props.EnumProperty(name='Display',
	 items=[	 
		 ('PLAIN_AXES', 'PLAIN_AXES', '', 0),
		 ('ARROWS', 'ARROWS', '', 1), 
		 ('SINGLE_ARROW', 'SINGLE_ARROW', '', 2),
		 ('CIRCLE', 'CIRCLE', '', 3),
		 ('CUBE', 'CUBE', '', 4),		
		 ('SPHERE', 'SPHERE', '', 5),
		 ('CONE', 'CONE', '', 6),
		 ('IMAGE', 'IMAGE', '', 7),
		 ],	 
		  default='PLAIN_AXES')
	forward_axis: bpy.props.EnumProperty(items=[
		('X', 'X', '', 0),
		('Y', 'Y', '', 1),
		('Z', 'Z', '', 2),
		('-X', '-X', '', 3),
		('-Y', '-Y', '', 4),
		('-Z', '-Z', '', 5)
		],
		name='Forward Axis', default='Z' )
	up_axis: bpy.props.EnumProperty(items=[
		('X', 'X', '', 0),
		('Y', 'Y', '', 1),
		('Z', 'Z', '', 2)],
		name='Up Axis', default='X')

	@classmethod
	def poll(cls, context):
		return context.object is not None and context.object.type == 'MESH'

	def draw(self, context):
		layout = self.layout
		column = layout.column()		
		column.prop(self, 'name')
		column.prop(self, 'scale')		
		column.prop(self, 'radius')
		column.prop(self, 'empty_display_type')		
		column.prop(self, 'align')	
		if self.align:
			column.prop(self, 'forward_axis')
			column.prop(self, 'up_axis')

	def add_empty(self, context, location, rotation, scale):
		empty = bpy.data.objects.new(self.name, None)
		context.layer_collection.collection.objects.link(empty)
		empty.empty_display_type = self.empty_display_type
		empty.empty_display_size = self.radius
		empty.rotation_mode = 'QUATERNION'
		empty.matrix_world = context.object.matrix_world @ Matrix.LocRotScale(location, rotation, scale)		
	
	def get_loop(self, v):
		loop = []
		def next_vert(v):			
			for e in v.link_edges:
				if e.select:
					next_vert = e.verts[0] if e.verts[0] is not v else e.verts[1]					
					e.select_set(False)
					return next_vert
			return None
		while v:			
			loop.append(v)
			v = next_vert(v)
		return loop

	def find_median_position(self, verts):
		if not len(verts) > 0:
			return Vector()
		
		pos_sum = Vector()
		for vert in verts:
			pos_sum += vert.co		
		return pos_sum * (1/len(verts))

	def execute(self, context):
		mesh = context.object.data

		if context.mode == 'OBJECT':
			bpy.ops.object.mode_set(mode = 'EDIT')

		bm = bmesh.from_edit_mesh(mesh)	
		bm.verts.ensure_lookup_table()
		bm.verts.index_update()
		
		# get loops
		verts = [v for v in bm.verts if v.select]
		loops = []
		unpacked_verts = set()

		for vert in verts:
			if vert not in unpacked_verts:
				loop = set(self.get_loop(vert))
				loops.append(list(loop))
				for v in loop:
					unpacked_verts.add(v)

		for loop in loops:			
			center = self.find_median_position(loop)		
			if len(loop) > 2:
				v1 = loop[0].co - loop[1].co
				v2 = loop[1].co - loop[2].co
				cross = v1.cross(v2).normalized()

				if self.forward_axis == self.up_axis:
					self.report({'WARNING'}, self.bl_idname + ': '  + 'Forward and Up can\'t be the same axis')	
					continue	
				
				self.add_empty(context, center, cross.to_track_quat(self.forward_axis, self.up_axis), None)

			else:
				self.report({'WARNING'}, self.bl_idname + ': ' + str(loop) + ' Loop can\'t have less than 3 points')
				continue

		return {'FINISHED'}	


class SocketInObjectPivotPosition(Operator):
	bl_idname = "object.socket_in_pivot"
	bl_label = "Socket in Object Pivot"
	bl_description = "Create Sockets in the objects' pivot positions"
	bl_options = {'REGISTER', 'UNDO'}

	@classmethod
	def poll(cls, context):
		return context.active_object is not None

	def execute(self, context):
		sel = bpy.context.selected_objects
		if len(sel):
			for i in sel:
				#get pivot position
				bpy.context.view_layer.objects.active = i
				pos = i.location
				#create empty
				bpy.ops.object.empty_add(type='PLAIN_AXES', radius=0.01, location = (pos))

				obj = bpy.context.active_object
				obj.name = 'SOCKET_' + i.name
				obj.rotation_euler[0] = i.rotation_euler[0]
				obj.rotation_euler[1] = i.rotation_euler[1]
				obj.rotation_euler[2] = i.rotation_euler[2]
		else:
			self.report({'WARNING'}, self.bl_idname + ": " + "Nothing selected!")

		return {'FINISHED'}

class RandomRotation(Operator):
	bl_idname = "object.rotate_random"
	bl_label = "Rotate objects with ramdom angle values along selected axis"
	bl_description = "Rotate objects with ramdom angle values along selected axis"
	bl_options = {'REGISTER', 'UNDO'}
	axis: bpy.props.IntProperty(options = {'HIDDEN'})

	@classmethod
	def poll(cls, context):
		return context.object is not None

	def execute(self, context):
		sel = bpy.context.selected_objects

		if len(sel):
			for obj in sel:
				obj.rotation_euler[self.axis] = uniform(0, 6.41)

		else:
			self.report({'WARNING'}, self.bl_idname + ": " + "Nothing selected!")

		return {'FINISHED'}

class GetUETransforms (Operator):
	bl_idname = "object.get_ue_transforms"
	bl_label = "Get UE Transforms"
	bl_description = "Copies transforms of the selected meshes/empties to the clipboard for manual pasting into UE Transform properties or text editor for editing"

	@classmethod
	def poll(cls, context):
		return context.object is not None

	def get_pivot(self, sel, context):
		avg = mathutils.Vector()
		for o in sel:
			avg += o.location

		return avg/len(sel)

	def execute(self, context):
		scene = context.scene
		sel = context.selected_objects
		buffer = StringIO()

		counter = 0

		offset = Vector((scene.copy_transform_offset[0], scene.copy_transform_offset[1], scene.copy_transform_offset[2]))

		if len(sel):
			if len(sel) > 1:
				buffer.write("(")
				buffer.seek(1)

			for obj in sel:
				default_rotation_mode = None

				if obj.rotation_mode != "QUATERNION":
					default_rotation_mode = copy.copy(obj.rotation_mode)
					obj.rotation_mode = "QUATERNION"

				if obj.type == "EMPTY" or obj.type == "MESH":
					buffer.write(
						"(Rotation=(X=" + str(obj.rotation_quaternion[1])
						+ ",Y=" +  str(obj.rotation_quaternion[2]* -1.0)
						+ ",Z=" + str(obj.rotation_quaternion[3]) + ",W="
						+ str(obj.rotation_quaternion[0]* -1.0) + "),"

						+ "Translation=(X=" + str((obj.location[0] + offset[0])*100)
						+ ",Y=" + str((obj.location[1] + offset[1])*-100)
						+ ",Z=" + str((obj.location[2] + offset[2])*100) + "),"

						+ "Scale3D=(X=" + str(obj.scale[0])
						+ ",Y=" + str(-obj.scale[1])
						+ ",Z=" + str(obj.scale[2]) + "))"
						)

					if (counter != len(sel) - 1):
						buffer.write(",\n")
						counter += 1

			if len(sel) > 1:
				buffer.write(")")

			if default_rotation_mode != None:
				obj.rotation_mode = default_rotation_mode

		buffer.seek(0)

		copy_cmd = str()
		if platform.system() == 'Windows':
			copy_cmd = 'clip'
		else:
			copy_cmd = 'pbcopy'

		if (copy_cmd):
			val = subprocess.run(copy_cmd, universal_newlines=True, input=buffer.read())
			if val is None:				
				self.report({'ERROR'}, "Can't perform copying to clipboard on current OS!")

		return {'FINISHED'}

class GetUETransform(Operator):
	bl_idname = 'object.get_ue_transform'
	bl_label = 'Get Transform'
	bl_description = 'Get UE Translation, Rotation or Scale from copied to clipboard Blender corresponding transformation'
	bl_options = {'REGISTER', 'UNDO'}
	
	type: bpy.props.EnumProperty(items=[
		('TRANSLATION', 'Translation', ''),
		('ROTATION', 'Rotation', ''),
		('SCALE', 'Scale', '',)], 
		name='Transformation',
		options={'HIDDEN'})

	@classmethod
	def poll(cls, context):
		return context.object is not None	

	def execute(self, context):
		obj = context.object
		wm = context.window_manager

		match self.type:
			case 'TRANSLATION':
				wm.clipboard = '(X=' + str(100*obj.location.x) \
							+ ',Y=' + str(-100*obj.location.y) \
							+ ',Z=' + str(100*obj.location.z) \
							+ ')'			
			case 'ROTATION':				
				wm.clipboard = '(Pitch=' + str(math.degrees(-float(obj.rotation_euler.y))) \
							+ ',Yaw=' + str(math.degrees(float(obj.rotation_euler.z))) \
							+ ',Roll=' + str(math.degrees(float(obj.rotation_euler.x))) \
							+ ')'
			case 'SCALE':
				wm.clipboard = '(X=' + str(obj.scale.x) \
							+ ',Y=' + str(obj.scale.y) \
							+ ',Z=' + str(obj.scale.z) \
							+ ')'


		return {'FINISHED'}

class SetUETransform(Operator):
	bl_idname = 'object.set_ue_transform'
	bl_label = 'Set Transform'
	bl_description = 'Set Blender Location, Rotation or Scale from copied to clipboard UE corresponding transformation'
	bl_options = {'REGISTER', 'UNDO'}

	type: bpy.props.EnumProperty(items=[
		('TRANSLATION', 'Translation', ''),
		('ROTATION', 'Rotation', ''),
		('SCALE', 'Scale', '',)], 
		name='Transformation',
		options={'HIDDEN'})

	@classmethod
	def poll(cls, context):
		return context.object is not None

	def execute(self, context):
		try:
			obj = context.object

			if obj.rotation_mode != 'XYZ':
				obj.rotation_mode = 'XYZ'

			data = re.sub('[A-Za-z=()]', '', context.window_manager.clipboard)
			x, y, z = data.split(',')

			match self.type:
				case 'TRANSLATION':				
					obj.location = 0.01*Vector((float(x), -float(y), float(z)))
				case 'ROTATION':
					obj.rotation_euler = Vector((math.radians(float(z)), math.radians(-float(y)), math.radians(float(x))))
				case 'SCALE':
					obj.scale = Vector((float(x), -float(y), float(z)))
		
		except:
			self.report({'ERROR'}, 'Clipboard does not contain valid transform data!')
			return {'CANCELLED'}
			
		return {'FINISHED'}

class GetUESplinePoints (Operator):
	bl_idname = "object.get_ue_spline_points"
	bl_label = ""
	bl_description = "Copies a spline parameters to the clipboard for manual pasting into UE Transform properties or text editor for editing"

	@classmethod
	def poll(cls, context):
		return context.object is not None and context.object.type == 'CURVE'

	def execute(self, context):
		scene = context.scene
		curve = context.selected_objects[0]
		buffer = StringIO("(")
		buffer.seek(1)
		counter = 0

		points = curve.data.splines[0].bezier_points[:]

		#offset = Vector((scene.copy_transform_offset[0], scene.copy_transform_offset[1],  scene.copy_transform_offset[2]))

		if len(points):
			for point in  points:
				position = (point.co)*100
				arrive_tangent = Vector((point.handle_left[0], point.handle_left[1], point.handle_left[2]))*100
				leave_tangent = Vector((point.handle_right[0], point.handle_right[1], point.handle_right[2]))*100

				buffer.write(
					"(InputKey=" + str(counter * 1.0) + ","

					+ "Position=(X=" + str(position[0])
					+ ",Y=" + str(-position[1])
					+ ",Z=" + str(position[2]) + "),"

					+ "ArriveTangent=(X=" + str((position[0] - arrive_tangent[0])*3)
					+ ",Y=" + str(-(position[1] - arrive_tangent[1])*3)
					+ ",Z=" + str((position[2] - arrive_tangent[2])*3) + "),"

					+ "LeaveTangent=(X=" + str((leave_tangent[0] - position[0])*3)
					+ ",Y=" + str(-(leave_tangent[1] - position[1])*3)
					+ ",Z=" + str((leave_tangent[2] - position[2])*3) + "))"
					)

				if (counter != len(points) - 1):
					buffer.write(",")
					counter += 1

			buffer.write(")")
			buffer.seek(0)

			copy_cmd = str()
			if platform.system() == 'Windows':
				copy_cmd = 'clip'
			else:
				copy_cmd = 'pbcopy'

			if (copy_cmd):
				val = subprocess.run(copy_cmd, universal_newlines=True, input=buffer.read())
				if val:
					self.report({'INFO'}, "Spline parameters have been copied to the clipboard. Paste them in appropriate UE Transform property")
				else:
					self.report({'ERROR'}, "Can't perform copying to clipboard on current OS!")

		else:
			self.report({'Warning'}, "Invalid curve!")

		return {'FINISHED'}

class GetCamsoSplinePoints (Operator):
	bl_idname = "object.get_camso_spline_points"
	bl_label = ""
	bl_description = "Copy spline point transforms to the clipboard for pasting into CamsoDynamicSplineComponent spline data property. Following naming numerial order is recommended *_01, *_02, *_03, ..."

	@classmethod
	def poll(cls, context):
		return context.object is not None and context.object.type == 'CURVE'

	def execute(self, context):
		scene = context.scene
		curves = sorted([obj for obj in context.selected_objects if obj.type=='CURVE'], key=lambda obj: obj.name)
		buffer = StringIO("")

		if curves:
			buffer.write("(")
			buffer.seek(1)

			curves_counter = 0
			for curve in curves:
				buffer.write("(Points=(\n")

				points = curve.data.splines[0].bezier_points[:]

				#offset = Vector((scene.copy_transform_offset[0], scene.copy_transform_offset[1], scene.copy_transform_offset[2]))

				if points:
					points_counter = 0

					for point in points:
						position = Vector((point.co[0], point.co[1], point.co[2]))*100
						arrive_tangent = Vector((point.handle_left[0], point.handle_left[1], point.handle_left[2]))*100
						leave_tangent = Vector((point.handle_right[0], point.handle_right[1], point.handle_right[2]))*100

						buffer.write(
							"\t(Position=(X=" + str(position[0])
							+ ",Y=" + str(-position[1])
							+ ",Z=" + str(position[2]) + "),\t"

							+ "ArriveTangent=(X=" + str((position[0] - arrive_tangent[0])*3)
							+ ",Y=" + str(-(position[1] - arrive_tangent[1])*3)
							+ ",Z=" + str((position[2] - arrive_tangent[2])*3) + "),\t"

							+ "LeaveTangent=(X=" + str((leave_tangent[0] - position[0])*3)
							+ ",Y=" + str(-(leave_tangent[1] - position[1])*3)
							+ ",Z=" + str((leave_tangent[2] - position[2])*3) + "))\t\n"
						)

						if (points_counter != len(points) - 1):
							buffer.write(",\t\n")
							points_counter += 1
						else:
							buffer.write("))")

				if (curves_counter != len(curves) - 1):
					buffer.write(",\t\n")
					curves_counter += 1

			buffer.write(")")
			buffer.seek(0)

			copy_cmd = str()
			if platform.system() == 'Windows':
				copy_cmd = 'clip'
			else:
				copy_cmd = 'pbcopy'

			if (copy_cmd):
				val = subprocess.run(copy_cmd, universal_newlines=True, input=buffer.read())
				if val:
					self.report({'INFO'}, str(curves) + ": spline data has been copied to the clipboard" )
				else:
					self.report({'ERROR'}, "Can't perform copying to clipboard on current OS!")
		else:
			self.report({'Warning'}, "Invalid curve!")

		return {'FINISHED'}

class GetUEBoneConstraints(Operator):
	bl_idname = "object.get_bone_constraints_transforms"
	bl_label = "Get Body Bone Constraints Transforms"
	bl_description = "Copies Body Bone Constraints Transforms in UE format into clipboard. Requires Armature selection. Paste them into the BodyPreview file"

	@classmethod
	def poll(cls, context):
		return context.object is not None and context.object.type == 'ARMATURE'

	def execute(self, context):
		armature = context.object
		sel = context.selected_objects
		if len(sel):
			for arm in sel:
				if arm.type == 'ARMATURE':
					bones_with_constraints = [bone for bone in context.object.pose.bones if len(bone.constraints)]
					bones_count = len(bones_with_constraints)
					buffer = StringIO("(")
					buffer.seek(1)
					counter = 0
					for bone in bones_with_constraints:
						constraints = bone.constraints["Limit Location"]
						buffer.write("(Name="
							+ "\""
							+ str(bone.name) + "\""
							+ ",Min=(X=" + str(round(constraints.min_x, 6)*100)
							+ ",Y=" + str(round(constraints.min_y, 6)* -100)
							+ ",Z=" + str(round(constraints.min_z, 6)*100)
							+ "),Max=(X=" + str(round(constraints.max_x, 6)*100)
							+ ",Y=" + str(round(constraints.max_y, 6)* -100)
							+ ",Z=" + str(round(constraints.max_z, 6)*100)
							+ "))")
						counter += 1
						if (counter < bones_count):
							buffer.write(",")
					buffer.write(")")
					buffer.seek(0)

					copy_cmd = str()
					if platform.system() == 'Windows':
						copy_cmd = 'clip'
					else:
						copy_cmd = 'pbcopy'

					if (copy_cmd):
						val = subprocess.run(copy_cmd, universal_newlines=True, input=buffer.read())
						if val:
							self.report({'INFO'}, "Transforms have been copied to the clipboard. Paste them in appropriate UE Transform property")
						else:
							self.report({'ERROR'}, "Can't perform copying to clipboard on current OS!")

		return {'FINISHED'}

# Utils
class GetPointsAngle(Operator):
	bl_idname = "mesh.get_points_angle"
	bl_label = "Get Points Angle"
	axis: bpy.props.FloatVectorProperty()
	# requires 3 points selected
	# active point is the mesh pivot point
	# 2 opposite points make the angle
	# bpy.ops.mesh.get_points_angle(axis=((-1,0,0)))

	@classmethod
	def poll(cls, context):
		return context.object is not None and context.object.type == 'MESH'

	def execute(self, context):
		obj = bpy.context.object
		bm = bmesh.from_edit_mesh(obj.data)
		bm.verts.ensure_lookup_table()

		alpha_point = bm.select_history.active

		verts = [v for v in bm.verts if v.select and v!=alpha_point]
		angle = verts[0].co.angle(verts[1].co)
		print ("Angle: ", (angle* 180/3.14159265359), "deg ")

		if angle > 0:
			bmesh.ops.rotate(
				bm,
				verts=bm.verts,
				cent=alpha_point.co,
				matrix=Matrix.Rotation(angle, 4, self.axis))

		bpy.ops.object.mode_set(mode = 'OBJECT')
		bpy.ops.object.mode_set(mode = 'EDIT')

		return {'FINISHED'}

class GenerateHierarchy(Operator):
	bl_label = 'Generate Hierarchy'
	bl_idname = 'object.generate_hierarchy'
	bl_description = 'Generate Collections for Car Parts'
	bl_options = {'REGISTER', 'UNDO'}
	collection_type: bpy.props.StringProperty(options={'HIDDEN'})

	@classmethod
	def poll(cls, context):
		return context.collection is not None

	def execute(self, context):
		collection = context.collection
		obj = bpy.context.object
		if self.collection_type == 'Body':
			list = ('Body Variants [Select for Batch Export]', 'New Body [Strictly 1 Body, 1 Bounds mesh]')
			generate_collections(self, context, list, 0, 1)

		elif self.collection_type == 'Rim':
			list = ('Rim Variants [Select for Batch Export]', 'New Rim [Any Rim mesh(es)]')
			generate_collections(self, context, list, 0, 1)

		elif self.collection_type == 'Fixture':
			list = ('Fixture Variants [Select for Batch Export]', 'New Fixture [Select for Single Export]', '_Conforming_Mesh', '_Skinned_Mesh', '_UV_Mesh')
			generate_collections(self, context, list, 1, 3)

		elif self.collection_type == 'LODs':
			at_create_lods_collection_hierarchy(obj.name if obj is not None else 'LODs', 2)

		return {'FINISHED'}

class AT_SelectRecursive(Operator):
	bl_idname = "object.hierarchy_select_recursive"
	bl_label = "Selects Parent and all its Children recursively"
	bl_options = {'REGISTER', 'UNDO'}

	@classmethod
	def poll(cls, context):
		return context.object is not None and context.object.type == 'EMPTY'

	def execute(self, context):
		select_recursive(self, context.object)
		return {'FINISHED'}

class ReloadAllTextures(Operator):
	bl_idname = "view3d.reload_all_textures"
	bl_label = "Reload All Textures"
	bl_options = {'REGISTER', 'UNDO'}

	def execute(self, context):
		if len(bpy.data.images[:]):
			for tex in bpy.data.images[:]:
				tex.reload()
		return {'FINISHED'}

class FixMaterialSlots(Operator):
	bl_idname = "object.fix_material_slots"
	bl_label = "Fix Material Slots"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = "Fix imported material slots"

	@classmethod
	def poll(cls, context):
		return context.object is not None and len(bpy.context.object.material_slots) > 0

	def do_replace(self, context, obj):
		PaintedSlots = ['AirFilter', 'IntakeManifold', 'IntakeManifoldTrim', 'Bolt', 'rocker_cover', 'rocker_cover_trim', 'AirFilterTrim', 'blockmaterial']

		elements = None
		with open(context.scene.json_materials_data_path, 'r') as json_data:
			elements = json.load(json_data)
		json_data.close()

		strings	= [material["materialInterface"] for material in elements]
		src = [e[e.find(".") + 1 : -1] for e in strings]

		slots = [slot["materialSlotName"] for slot in elements]
		slot_dict = dict(zip(slots, src))
		print ("*** UE slot name : material name: ", slot_dict)

		print("*** UE materials stack:", src)

		if (len(elements) == len(obj.data.materials) and len(obj.data.materials) > 0):
			index = 0
			if obj and obj.type == 'MESH' and len(obj.material_slots) > 0:
				mat_list = obj.data.materials[:]
				for i in mat_list:
					#replace
					if (i.name not in PaintedSlots):
						if i.name != src[index] and src[index] in  bpy.data.materials:
							obj.data.materials[index] = bpy.data.materials[src[index]]
						else:
							obj.data.materials[index].name = src[index]

					index += 1
		else:
			self.report({'WARNING'},  "Mesh materials count doesn't match! Make sure UE json material data file is relevant")

	def execute(self, context):
		sel = bpy.context.selected_objects
		if sel:
			for obj in sel:
				bpy.context.view_layer.objects.active = obj
				self.do_replace(context, obj)
		else:
			self.do_replace(context, bpy.context.object)

		return {'FINISHED'}

class DuplicateOffset(Operator):
	bl_idname = "object.duplicate_offset"
	bl_label = "Duplicate with linear offset"
	bl_options = {'REGISTER', 'UNDO'}

	@classmethod
	def poll(cls, context):
		return context.object is not None and len(context.scene.transform_orientation_slots) > 0

	count: bpy.props.IntProperty(name='Count', default=1)
	offset: bpy.props.FloatVectorProperty(name='Offset', step=10)
	is_linked: bpy.props.BoolProperty(name='Link', default=True)
	orient: bpy.props.EnumProperty(items=[
		('GLOBAL', 'Global', '', 'ORIENTATION_GLOBAL', 0),
		('LOCAL', 'Local', '', 'ORIENTATION_LOCAL', 1),
		('SCENE', 'Scene', 'Scene Active Transform Orientation', 'OBJECT_ORIGIN', 2),	
		('NORMAL', 'Normal', '', 'ORIENTATION_NORMAL', 3),
		('GIMBAL', 'Gimbal', '', 'ORIENTATION_GIMBAL', 4),
		('VIEW', 'View', '', 'ORIENTATION_VIEW', 5),
		('CURSOR', 'Cursor', '', 'ORIENTATION_CURSOR', 6),
		('PARENT', 'Parent', '', 'ORIENTATION_PARENT', 7),
		], 
		name='Orient' )

	def execute(self, context):
		for i in range(0, self.count):
			bpy.ops.object.duplicate_move(OBJECT_OT_duplicate={"linked":self.is_linked}, TRANSFORM_OT_translate={"value":self.offset, "orient_type":{True: context.scene.transform_orientation_slots[0].type, False: self.orient} [self.orient=='SCENE'] })

		return {'FINISHED'}

class DuplicateCircular(Operator):
	bl_idname = "object.duplicate_circular"
	bl_label = "Duplicate around circle"
	bl_options = {'REGISTER', 'UNDO'}

	count: bpy.props.IntProperty(name='Count')
	axis: bpy.props.IntProperty(name='Axis')
	is_linked: bpy.props.BoolProperty(name='Is Linked')

	def execute(self, context):
		pi = 3.141592653589
		axis_char = ''

		if self.axis == 0:
			 axis_char = 'X'
		elif self.axis == 1:
			axis_char = 'Y'
		elif self.axis == 2:
			axis_char = 'Z'
		else:
			return {'FINISHED'}

		for i in range(0, self.count-1):
			 bpy.ops.object.duplicate_move(OBJECT_OT_duplicate={"linked":self.is_linked, "mode":'TRANSLATION'})
			 bpy.ops.transform.rotate(value=(2*pi)/self.count, orient_axis=axis_char)

		return {'FINISHED'}

class FindDataUsers(Operator):
	bl_idname = "view3d.find_data_users"
	bl_label = "Find Data Users"
	bl_description = 'Find Data Users'
	
	data: bpy.props.StringProperty(name='Data', default='')

	def invoke(self, context, event):
		obj = context.object
		if  obj and obj.data:
			self.data = context.object.data.name

		wm = context.window_manager
		return wm.invoke_props_dialog(self)

	def execute(self, context):
		find_data_users(self, self.data)
		return {'FINISHED'}

def find_data_users(cls, name):
		objects_collection = bpy.data.objects
		users = []
		
		for obj in objects_collection.values():
			if obj.data and obj.data.name == name:
				users.append(obj)		
		
		print('\n')		
		print ('Users: ' + str(len(users)))

		if users:
			for user in users:
				for scene in bpy.data.scenes:					
					if user.name in scene.objects.keys():						
						print(scene.name, '->', user.name)

class AT_ResetTransform(Operator):
	bl_idname = 'object.at_reset_transform'
	bl_label = 'Reset Transform'
	bl_description = 'Set transform to default'
	bl_options = {'REGISTER', 'UNDO'}
	
	@classmethod
	def poll(cls, context):
		return context.object is not None

	def execute(self, context):
		for obj in bpy.context.selected_objects:
			obj.location = Vector()
			obj.rotation_euler = Euler()
			obj.rotation_quaternion = Quaternion()
			obj.scale = Vector((1,1,1))

		return {'FINISHED'}	

class AT_SnapCurveToTarget(Operator):
	bl_idname = 'curve.snap_curve_to_target'
	bl_label = 'Snap Curve To Target'
	bl_description = "Snaps Bezier curve\'s end point to a mesh point"
	bl_options = {'REGISTER', 'UNDO'}

	vertex_index: bpy.props.IntProperty(name='Vertex Index')
	point_index: bpy.props.IntProperty(name='Point Index', min=-1, max=0)
	handle_inverse: bpy.props.BoolProperty(name='Handle Inverse')
	rotate_90: bpy.props.BoolProperty(name='Rotate Handle 90 degrees')
	
	@classmethod
	def poll(cls, context):
		return context.object is not None

	def execute(self, context):
		sel = context.selected_objects

		if len(sel) != 2:
			self.report({'ERROR'},  "Select 2 objects - a curve and a target mesh")
			return {'CANCELLED'}
		
		if sel[0].type != 'CURVE':
			sel[0], sel[1] = sel[1], sel[0]

		curve = sel[0]
		target_obj = sel[1]

		if target_obj.type != 'MESH' or curve.type != 'CURVE':
			self.report({'ERROR'},  "Active object must be a curve and the second selected object a mesh")
			return {'CANCELLED'}

		depsgraph = context.evaluated_depsgraph_get()

		vertex_index = self.vertex_index
		point_index = self.point_index

		target_obj.rotation_mode = 'QUATERNION'

		target_location = target_obj.matrix_world@target_obj.data.vertices[vertex_index].co
		target_orientation = target_obj.rotation_quaternion.to_matrix()
		
		spline = curve.data.splines[0]
		point = spline.bezier_points[point_index]
		matrix = curve.matrix_world

		translation = Matrix.Translation(target_location - (matrix@point.co))
		target_direction = ((0.01 * (target_orientation))@(Vector((0,0,1))) + target_location)
		point.co = matrix.inverted()@(translation@(matrix@point.co))
		point.handle_left_type = 'FREE'
		point.handle_left = matrix.inverted()@(target_direction)
		
		if self.handle_inverse:
			point.handle_left = (-1*(point.handle_left - point.co)) + point.co

		if self.rotate_90:
			handle = (point.handle_left - point.co)
			point.handle_left = handle.orthogonal() + point.co

		point.handle_right = point.handle_left

		return {'FINISHED'}

class AT_SnapRotateMeshToTarget(Operator):
	bl_idname = 'mesh.at_snap_rotate'
	bl_label = 'Snap Rotate Mesh To Target'
	bl_description = 'Rotate mesh to snap to scene cursor like a dial. Mesh must have 3 vertices selected. Origin must be located in the center or rotation. The active vertex is the target, the others are used for finding rotation axis. Selected vertices create the rotation axis plane'
	bl_options = {'REGISTER', 'UNDO'}

	@classmethod
	def poll(cls, context):
		return context.object is not None and context.object.type == 'MESH'
	
	def execute(self, context):
		bpy.ops.object.mode_set(mode = 'OBJECT')
		bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)		
		obj = context.object				
		mesh = obj.data
		matrix = obj.matrix_world
		cursor = context.scene.cursor
		
		bm = bmesh.new()
		bm.from_mesh(mesh)
		bm.verts.ensure_lookup_table()		
		bm.verts.index_update()
		verts = [vert.co for vert in bm.verts]	
		sel = [vert for vert in bm.verts if vert.select]

		if verts is None:			
			return {'CANCELLED'}

		if not len(sel) > 2:			
			self.report({'ERROR'}, self.__class__.__name__ + ': '  + 'Mesh must have al least 3 selected vertices!')
			return{'CANCELLED'}		
			
		vert_target = matrix@bm.select_history[-1].co		

		if obj.rotation_mode != 'QUATERNION':
			obj.rotation_mode = 'QUATERNION'

		# rotation axis
		v1 = sel[0].co - sel[1].co
		v2 = sel[1].co - sel[2].co
		axis = v1.cross(v2).normalized()

		cursor_target = cursor.location - obj.location

		quat = (vert_target - obj.location).rotation_difference(cursor_target)
		obj.matrix_world = obj.matrix_world@quat.to_matrix().to_4x4()

		bm.free()
		
		bpy.ops.object.mode_set(mode = 'EDIT')

		return {'FINISHED'}

class AT_SnapRotateVertsToTarget(Operator):
	bl_idname = 'mesh.at_snap_rotate_verts'
	bl_label = 'Snap Rotate Mesh To Target'
	bl_description = 'Rotate and snap selected vertices scene cursor like a dial. Mesh must have at least 3 selected vertices'
	bl_options = {'REGISTER', 'UNDO'}

	@classmethod
	def poll(cls, context):
		return context.object is not None and context.object.type == 'MESH' and context.mode == 'EDIT_MESH'
	
	def execute(self, context):	
		obj = context.object
		mesh = obj.data
		matrix = obj.matrix_world
		cursor = context.scene.cursor	
		
		bm = bmesh.from_edit_mesh(mesh)
		target_vertex = bm.select_history.active		
		
		if target_vertex is None or not isinstance(target_vertex, bmesh.types.BMVert):
			self.report({'ERROR'}, self.__class__.__name__  + ': Target element is not a vertex!')
			return{'CANCELLED'}

		bm.verts.ensure_lookup_table()		
		bm.verts.index_update()

		verts = [vert.co for vert in bm.verts]	
		sel = [vert for vert in bm.verts if vert.select]

		if verts is None:			
			return {'CANCELLED'}

		if not len(sel) > 2:			
			self.report({'ERROR'}, self.__class__.__name__  + ': Mesh must have al least 3 selected vertices!')
			return{'CANCELLED'}		

		if not len(bm.select_history) > 0:	
			self.report({'ERROR'}, self.__class__.__name__  + ': No active vertex!')
			return{'CANCELLED'}			
			

		target_vertex_position = target_vertex.co
		
		rotation_origin = calculate_median([vert.co for vert in sel])
		cursor_position = (matrix.inverted()@cursor.location) - rotation_origin
		target_vertex_position = target_vertex_position - rotation_origin
		quat = cursor_position.rotation_difference(target_vertex_position)	

		for vert in sel:
			v = vert.co - rotation_origin
			v.rotate(quat.inverted())
			vert.co = v + rotation_origin

		update_object_edit(context)

		return {'FINISHED'}

class AT_SnapBezierPointToCursor(Operator):
	bl_idname = 'curve.snap_bezier_point_to_cursor'
	bl_label = 'Snap Bezier Point To Cursor'
	bl_description = "Snap selected points and align their handles to scene cursor position and orientation"
	bl_options = {'REGISTER', 'UNDO'}
	snap_point: bpy.props.BoolProperty(name='Snap point', default=True)
	align_handle_right: bpy.props.BoolProperty(name='Align Handle Right', default=True)
	align_handle_left: bpy.props.BoolProperty(name='Align Handle Left', default=True)
	# handle_inverse: bpy.props.BoolProperty(name='Inverse Handles')
	
	@classmethod
	def poll(cls, context):
		return context.object is not None and context.object.type == 'CURVE'

	def execute(self, context):
		curve = context.object
		spline = curve.data.splines[0]
	
		if spline.type != 'BEZIER':
			self.report({'ERROR'},  "Selected spline type must be a Bezier!")
			return {'CANCELLED'}

		sel = [point for point in spline.bezier_points if point.select_control_point]

		depsgraph = context.evaluated_depsgraph_get()

		cursor = context.scene.cursor
		if cursor.rotation_mode != 'QUATERNION':
			cursor.rotation_mode = 'QUATERNION'
		
		target_orientation = cursor.rotation_quaternion.to_matrix()
		target_location = cursor.location
		matrix = curve.matrix_world

		for point in sel:
			if self.snap_point:
				translation = Matrix.Translation(target_location - (matrix@point.co))
				point.co = matrix.inverted()@(translation@(matrix@point.co))
			
			target_direction = ((0.01 * target_orientation)@(Vector((0,0,1))) + target_location)			
			point.handle_left_type = 'FREE'
			if self.align_handle_left:
				point.handle_left = matrix.inverted()@(target_direction)
			
			if self.align_handle_right:
				point.handle_right = matrix.inverted()@target_direction
			
			# if self.handle_inverse:
			# 	point.handle_left = (-1*(point.handle_left - point.co)) + point.co

			# point.handle_right = point.handle_left

		return {'FINISHED'}

class AT_SetMeshPositionToZero(Operator):
	bl_idname = 'mesh.at_set_mesh_position_to_zero'
	bl_label = 'Set Mesh Position To Zero'
	bl_description = 'Set Mesh Position To Zero'
	bl_options = {'REGISTER', 'UNDO'}

	axis: bpy.props.BoolVectorProperty(subtype='XYZ', name='Axis')#,options={'SKIP_SAVE'}

	@classmethod
	def poll(cls, context):
		return context.object is not None

	def draw(self, context):
		layout = self.layout
		column = layout.column()
		row = column.row(align=True)
		row.prop(self, 'axis', toggle=True)

	def execute(self, context):	
		axis = self.axis

		if context.mode == 'EDIT_MESH':
			for obj in context.selected_objects:
				mesh = obj.data					
				bm = bmesh.from_edit_mesh(mesh)
				bm.verts.ensure_lookup_table()		
				bm.verts.index_update()					
				verts = [vert for vert in bm.verts if vert.select]

				if not len(verts) > 0:
					self.report({'WARNING'}, self.__class__.__name__  + ': No selected vertices!')
					continue

				median = calculate_median([vert.co for vert in verts])
				offset = Matrix.Translation(-median)
				
				for vert in verts:
					position = offset@vert.co					
					vert.co =  Vector((	
						position.x if axis[0] else vert.co.x,
						position.y if axis[1] else vert.co.y,
						position.z if axis[2] else vert.co.z
						))

			update_object_edit(context)

		elif context.mode == 'OBJECT':
			for obj in context.selected_objects:
				location = obj.location
				obj.location = Vector((
							0 if axis[0] else location.x,
							0 if axis[1] else location.y,
							0 if axis[2] else location.z
							))

		return {'FINISHED'}

class AT_SnapCursorToSelectedVerts(Operator):
	bl_idname = 'view3d.at_snap_cursor_to_selected_verts'
	bl_label = 'Snap Cursor To Selected Verts'
	bl_description = 'Snap Cursor To Selected Verts'
	bl_options = {'REGISTER', 'UNDO'}

	axis: bpy.props.BoolVectorProperty(subtype='XYZ', name='Axis', options={'SKIP_SAVE'})
	
	@classmethod
	def poll(cls, context):
		return context.object is not None and context.object.type == 'MESH'

	def draw(self, context):
		layout = self.layout
		column = layout.column()
		row = column.row(align=True)
		row.prop(self, 'axis', toggle=True)

	def execute(self, context):
		obj = context.object
		mesh = obj.data
		matrix = obj.matrix_world
		cursor = context.scene.cursor
		location = cursor.location.copy()		
		
		bpy.ops.object.mode_set(mode='OBJECT')
		bm = bmesh.new()
		bm.from_mesh(mesh)
		
		bm.verts.ensure_lookup_table()
		bm.verts.index_update()

		verts = [vert.co for vert in bm.verts if vert.select]		
		
		if not len(verts) > 0:
			self.report({'WARNING'}, self.__class__.__name__  + ': No selected vertices!')
			return{'CANCELLED'}
		
		target = matrix@(calculate_median(verts) if len(verts) > 1 else verts[0])

		bm.free()	

		cursor.location = Vector((
							target.x if self.axis[0] else location.x,
							target.y if self.axis[1] else location.y,
							target.z if self.axis[2] else location.z
							))

		bpy.ops.object.mode_set(mode='EDIT')

		return {'FINISHED'}

class AT_CursorToZero(Operator):
	bl_idname = 'view3d.at_set_cursor_position_to_zero'
	bl_label = 'Set Cursor Position To Zero'
	bl_description = 'Set Cursor Position To Zero'
	bl_options = {'REGISTER', 'UNDO'}

	axis: bpy.props.BoolVectorProperty(subtype='XYZ', name='Axis', options={'SKIP_SAVE'})
	
	def draw(self, context):
		layout = self.layout
		column = layout.column()
		row = column.row(align=True)
		row.prop(self, 'axis', toggle=True)
	
	def execute(self, context):
		cursor = context.scene.cursor
		location = cursor.location.copy()	
		axis = self.axis

		cursor.location = Vector((
							0 if axis[0] else location.x,
							0 if axis[1] else location.y,
							0 if axis[2] else location.z
							))

		return {'FINISHED'}

class FixUVMapName(Operator):
	bl_idname = 'object.fix_uv_map_name'
	bl_label = 'Fix UVMap Name'
	bl_description = 'Fix UVMap Name'
	bl_options = {'REGISTER', 'UNDO'}

	@classmethod
	def poll(cls, context):
		return context.object is not None

	def execute(self, context):
		context.object.data.uv_layers[0].name = 'UVMap'
		return {'FINISHED'}

class HideLods(Operator):
	bl_idname = 'outliner.auto_hide_lods'
	bl_label = 'Hide LODs'
	lod_level : bpy.props.StringProperty(options={'HIDDEN'})
	bl_options = {'REGISTER', 'UNDO'}
	
	def execute(self, context):
		hide_lods(self, context, self.lod_level)
		return {'FINISHED'}

def hide_lods(cls, context, lod_level):
	collections = context.collection.children_recursive

	def do_hide(collection):
		for lod in collection.objects:
			if lod.type == 'EMPTY' and lod_level in lod.name:
				if len(lod.children) > 0:				
					for child_lod in lod.children:
						child_lod.hide_viewport = not child_lod.hide_viewport					
					lod.hide_viewport = not lod.hide_viewport

	if len(collections) > 0:
		for collection in collections:
			do_hide(collection)			
	
	elif len(collections) == 0:
		do_hide(context.collection)

def hide_lods_menu(self, context):
	layout = self.layout
	layout.separator()
	layout.operator(HideLods.bl_idname, text = 'LOD0').lod_level = 'LOD0'
	layout.operator(HideLods.bl_idname, text = 'LOD1').lod_level = 'LOD1'
	layout.operator(HideLods.bl_idname, text = 'LOD2').lod_level = 'LOD2'

def at_create_lods_collection_hierarchy(name, lods_count):
	root = bpy.data.collections.new(name)
	bpy.context.scene.collection.children.link(root)

	for index in range(lods_count):
		lod = bpy.data.collections.new('LOD'+str(index))
		root.children.link(lod)

def update_object_edit(context):
	if context.object is not None:
		bpy.ops.object.mode_set(mode = 'OBJECT')
		bpy.ops.object.mode_set(mode = 'EDIT')

def update_edit_object(context):
	if context.object is not None:
		bpy.ops.object.mode_set(mode = 'EDIT')
		bpy.ops.object.mode_set(mode = 'OBJECT')

def update_edit_object_edit(context):
	if context.object is not None:
		bpy.ops.object.mode_set(mode = 'EDIT')
		bpy.ops.object.mode_set(mode = 'OBJECT')
		bpy.ops.object.mode_set(mode = 'EDIT')	

def update_object_edit_object(context):
	if context.object is not None:
		bpy.ops.object.mode_set(mode = 'OBJECT')
		bpy.ops.object.mode_set(mode = 'EDIT')
		bpy.ops.object.mode_set(mode = 'OBJECT')

def create_bmesh(cls, context):
	update_object_edit()
	bm = bmesh.new()
	bm.from_mesh(context.object.data)
	return bm

def duplicate(cls, context, obj):
	obj.select_set(True)
	bpy.context.view_layer.objects.active = obj
	bpy.ops.object.duplicate()
	bpy.ops.object.select_all(action='DESELECT')
	return context.active_object

def get_faces_indicies(cls, obj):
	# called by the class only
	bpy.ops.object.mode_set(mode = 'EDIT')
	bm = bmesh.from_edit_mesh(obj.data)
	pos = [f.index for f in bm.faces]
	bpy.ops.object.mode_set(mode = 'OBJECT')
	return pos

def select_mirrored_faces(cls, obj, indicies):
	bm = bmesh.from_edit_mesh(obj.data)
	bpy.ops.mesh.select_mode(type='FACE')

	mirrored_faces = [f for f in bm.faces]
	for f in mirrored_faces:
		for match in indicies:
			if f.index == match:
				f.select = True
	bm.select_flush(True)
	bmesh.update_edit_mesh(obj.data)
	# invert
	bpy.ops.mesh.select_all(action='INVERT')

def fix_mirrored_half_triangulation(cls, obj, indicies):
	if 'Triangulate' in obj.modifiers:
		if obj.modifiers['Triangulate'].quad_method != 'FIXED':
			obj.modifiers['Triangulate'].quad_method = 'FIXED'

		bpy.ops.object.mode_set(mode = 'EDIT')
		bpy.ops.mesh.select_all(action='DESELECT')

		select_mirrored_faces(cls, obj, indicies)

		bpy.ops.mesh.rotate_edge_triangulation_quads(quad_method="FIXED_ALTERNATE")
		bpy.ops.object.mode_set(mode='OBJECT')

def generate_collections(cls, context, list, parent_index, children_count):
	_collection_ = bpy.context.collection
	_collections_= bpy.data.collections
	# generate
	if list[0] not in bpy.data.collections and list[0] not in 'Master Collection':
		for collection in list:
			_collections_.new(name = collection)
		# link
		if parent_index > 0:
			_collection_.children.link(_collections_[list[0]])
			_collections_[list[0]].children.link(_collections_[list[parent_index]])
		else:
			_collection_.children.link(_collections_[list[0]])

		for c in range(children_count):
			_collections_[list[parent_index]].children.link(_collections_[list[(-1 - c)]])

def bevel_width_input_menu(self, context):
	if context.object:
		if "bevel_width_driver" in context.object and len(context.object.animation_data.drivers):
			layout = self.layout
			row = layout.row()
			split = row.split(factor=0.75, align=True)
			split.prop(context.object, '["bevel_width_driver"]', text = 'Bevel Width')
			split.operator(BevelWidthLerpInputBar.bl_idname, text = 'Apply')

def scale_uv_checker(self, context):
	scale = context.scene.checker_scale
	mapping_node = context.object.active_material.node_tree.nodes.get('Mapping')
	mapping_node.inputs[3].default_value = (scale, scale, scale)
	return None

def select_recursive(cls, parent):
	for child in parent.children:
		if child.hide_viewport == False:
			child.select_set(True)
			if child.children:
				select_recursive(cls, child)

def select_parents_recursive(cls, parent):
	for child in parent.children:
		if child.type == 'EMPTY' and child.hide_viewport == False:
			child.select_set(True)
			if child.children:
				select_parents_recursive(cls, child)

def find_free_name(cls, context, collection, name):
	if name not in collection:
		return name
	else:
		return	find_free_name(cls, context, collection, name + " ")

def calculate_median(vectors):
	if not len(vectors) > 1:
		return None
	return sum(vectors, Vector())/len(vectors)

class AT_ObjectPointer(bpy.types.PropertyGroup):
	value: bpy.props.PointerProperty(type=bpy.types.Object)
	def is_valid(self):
		return self.value != None

# A utility operator to get selection list ordered by individual selection event
class AT_ObjectsSelectionHistory(Operator):
	bl_idname = 'scene.at_objects_selection_history'
	bl_label = 'Objects Selection History'
	bl_description = 'Records objects selection order in the scene'
	bl_options = {'REGISTER', 'UNDO'}
	selected_objects = []
	
	def start(self):
		bpy.context.view_layer.objects.active = None
		for obj in bpy.context.selected_objects:
			obj.select_set(False)

		subscribe_to = (bpy.types.LayerObjects, 'active')
		
		def msgbus_callback():
			obj = bpy.context.active_object
			if(obj is not None):
				self.selected_objects.append(obj)								
				# print('['+ obj.name + ']')
				# print(self.selected_objects)

		bpy.msgbus.subscribe_rna(
		key = subscribe_to,
		owner = bpy,
		args = (),
		notify = msgbus_callback
		)

	def stop(self):		
		bpy.msgbus.clear_by_owner(bpy)

	def print(self):
		print(self.bl_label + ':')		
		for obj in self.selected_objects:
			if obj is not None:
				print(obj.name)
			else:
				print('None')

	def invoke(self, context, event):
		context.workspace.status_text_set('[LMB]:SELECT  [ENTER]:FINISH  [ESC]:EXIT')
		if context.space_data.type == 'VIEW_3D':
			context.window_manager.modal_handler_add(self)
			self.start()
		else:
			self.report({'WARNING'}, "Current space is not 'VIEW_3D'")
			return {'CANCELLED'}
		return {'RUNNING_MODAL'}

def numerate(sel, lods):
	bpy.ops.object.name_with_spaces()
	for index, obj in enumerate(sel):
		if obj is not None:
			if not lods:
				obj.name = (obj.name + '_' +  '0' + str(index+1)) if index < 9 else (obj.name + '_' + str(index+1))
			else:
				obj.name = (obj.name + '_LOD' + str(index))
			if ' ' in obj.name:
				obj.name = obj.name.replace(' ', '')

class AT_NumerateOrdered(AT_ObjectsSelectionHistory):
	bl_idname = 'object.at_numerate_ordered'
	bl_label = 'AT Numerate Ordered'
	bl_description = "Numerates objects based on their selection order/history"
	bl_options = {'REGISTER', 'UNDO'}

	def modal(self, context, event):
		if (event.alt and event.type in {'LEFTMOUSE', 'RIGHTMOUSE', 'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE'}) or (event.type in {'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE'}):
			return {'PASS_THROUGH'}

		elif event.type == 'LEFTMOUSE':
			return {'PASS_THROUGH'}

		elif event.type == 'RET' and event.value == 'PRESS':			
			self.stop()
			numerate(self.selected_objects, False)
			self.selected_objects.clear()
			context.workspace.status_text_set(None)
			return {'FINISHED'}

		elif event.type == 'ESC' and event.value == 'PRESS':
			self.stop()
			self.selected_objects.clear()
			context.workspace.status_text_set(None)
			return {'FINISHED'}

		return {'RUNNING_MODAL'}

class AT_NumerateLODsOrdered(AT_ObjectsSelectionHistory):
	bl_idname = 'object.at_numerate_lods_ordered'
	bl_label = 'AT Numerate LODs Ordered'
	bl_description = "Numerates LODS based on their selection order/history"
	bl_options = {'REGISTER', 'UNDO'}

	def modal(self, context, event):
		if (event.alt and event.type in {'LEFTMOUSE', 'RIGHTMOUSE', 'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE'}) or (event.type in {'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE'}):
			return {'PASS_THROUGH'}

		elif event.type == 'LEFTMOUSE':
			return {'PASS_THROUGH'}

		elif event.type == 'RET' and event.value == 'PRESS':			
			self.stop()
			numerate(self.selected_objects, True)
			self.selected_objects.clear()
			context.workspace.status_text_set(None)
			return {'FINISHED'}

		elif event.type == 'ESC' and event.value == 'PRESS':
			self.stop()
			self.selected_objects.clear()
			context.workspace.status_text_set(None)
			return {'FINISHED'}

		return {'RUNNING_MODAL'}

class AT_Numerate(Operator):
	bl_idname = 'object.at_numerate'
	bl_label = ' AT Numerate'
	bl_description = "Numerate objects in their default Blender selection list order. Adds a number in the end of each element"
	bl_options = {'REGISTER', 'UNDO'}
	lods: bpy.props.BoolProperty(name='LODs')

	def execute(self, context):
		numerate(context.selected_objects, self.lods)
		return {'FINISHED'}

class SwitchScenes(Operator):
	bl_idname = 'view3d.switch_scenes'
	bl_label = 'Switch Scenes'
	bl_description = ''	
	bl_options = {'REGISTER', 'UNDO'}
	index: bpy.props.IntVectorProperty(name='Index', size=2, default=(0,1))
	
	def execute(self, context):
		index = self.index
		if context.scene == bpy.data.scenes[index[0]]:    
			context.window.scene = bpy.data.scenes[index[1]]
		elif context.scene == bpy.data.scenes[index[1]]:
			context.window.scene = bpy.data.scenes[index[0]]

		if 'bl_ext.blender_org.stored_views' in context.preferences.addons:
			if bpy.ops.view3d.stored_views_initialize.poll():
				bpy.ops.view3d.stored_views_initialize()

			if bpy.ops.stored_views.set.poll():
				bpy.ops.stored_views.set(index=0)

		return{'FINISHED'}
			

classes = (
	CopyApplyModifier,
	ToggleModifiersByType,
	ToggleAllModifiersVisibility,
	TransferModifiers,
	AddBevelWidthDriver,
	BevelWidthLerpInputBar,
	ApplyModifierShapeKeys,
	RotateEdgeTriangulationQuads,
	LightsUnwrap,
	ObjectFixName,
	FixMaterialName,
	AddBodyMaterials,
	AddFixtureMaterials,
	ClearMatSlots,
	CleanUpUnusedMatsMesh,
	CleanUpMatsScene,
	CleanUpMatsSceneAll,
	ResetNormalsObject,
	ToggleZeroOneValuesActiveShapeKey,
	ToggleZeroOneValuesVertexWeight,
	AddEmptyShapeKeys,
	ToggleCarPaint,
	GenerateHierarchy,
	CopyObjectName,
	PasteObjectName,
	NameForBake,
	CreateGroup,
	MoveToSceneCenter,
	AddEmptyInComponentSelectionCenter,
	SocketInObjectPivotPosition,
	AT_UVUnwrap,
	ScaleUVs,
	UVSeamsFromHardEdges,
	UnwrapCylinder,
	UnwrapPipe,
	CreateUVChecker,
	ToggleUVChecker,
	UVRotate,
	UVMirror,
	ReplaceMaterials,
	CreateCollection,
	ReplaceMaterialsGetter,
	ReplaceMaterialsAdder,
	SnapUVBottomsUVs,
	RandomRotation,
	GetUETransforms,
	GetUETransform,
	SetUETransform,
	GetUEBoneConstraints,
	GetUESplinePoints,
	GetCamsoSplinePoints,
	TransferTransform,
	ReloadAllTextures,
	GenerateIDColors,
	SwapObjectNames,
	AT_SelectRecursive,
	GetPointsAngle,
	InvertVertexColors,
	FillVertexColors,
	ConvertAOtoExhaustHeatMap,
	ChangeVertexColorBrightness,
	FixMaterialSlots,
	DuplicateOffset,
	DuplicateCircular,
	CopyObjectNameToDataName,
	FixObjectNameAndAddEndSpaces,
	FixCollectionNameAndAddEndSpaces,
	ObjectNameRemoveSpaces,
	AutomationRename,
	AutomationRename_CopyName,
	FindDataUsers,
	HideLods,
	FixUVMapName,
	RemoveDuplicates,
	AT_MarkSeams,
	AddEmptyInLoop,
	AT_ResetTransform,
	AT_SnapCurveToTarget,
	AT_SnapBezierPointToCursor,
	AT_ObjectPointer,
	AT_NumerateOrdered,
	AT_Numerate,
	AT_NumerateLODsOrdered,
	AT_SnapRotateMeshToTarget,
	AT_SnapRotateVertsToTarget,
	AT_SetMeshPositionToZero,
	AT_SnapCursorToSelectedVerts,
	AT_CursorToZero,
	SwitchScenes
)

# Register
def register():
	for cls in classes:
		bpy.utils.register_class(cls)

	bpy.types.OUTLINER_MT_collection_visibility.append(hide_lods_menu)	

	bpy.types.Scene.src_mat = bpy.props.StringProperty()
	bpy.types.Scene.trg_mat = bpy.props.StringProperty()

	bpy.types.Scene.checker_scale = bpy.props.FloatProperty(description = 'Scale Checker Texture. Textured Mode only', default = 1.0, min = 1.0, max = 10.0, update = scale_uv_checker)
	bpy.types.Scene.texel_value = bpy.props.FloatProperty(description = 'UV size value. Default Automation UV size is 50, which is 1x1 scene unit = 128x128 px texture', default = 50.0)

	bpy.types.Scene.modifiersVisibilityStateAll = bpy.props.BoolProperty()
	bpy.types.Scene.apply_uv_scale = bpy.props.BoolProperty(default=True, description='Unwrap will automatically apply UV scale. Use Get/Set methods to scale uvs manually. By default Blender automatic unwrap/scale is used. Texel density 50.0 is used as a default uv scale for many Automation assets with tiling uvs')

	bpy.types.Scene.copy_transform_offset = bpy.props.FloatVectorProperty(name='', description='Copy Transform Offset')

	#add buttons to Properties > Modifiers
	bpy.types.DATA_PT_modifiers.append(bevel_width_input_menu)

	bpy.types.Scene.new_object_name_input = bpy.props.StringProperty(name='', default='', description='Rename to')
	bpy.types.Scene.new_collection_name_input = bpy.props.StringProperty(name='', default='', description='Rename to')

	bpy.types.Scene.json_materials_data_path = bpy.props.StringProperty(
		name="",
		subtype='FILE_PATH',
		description = 'UE materials data File Path'
	)	


# Unregister
def unregister():
	for cls in reversed(classes):
		bpy.utils.unregister_class(cls)

	bpy.types.OUTLINER_MT_collection_visibility.remove(hide_lods_menu)
	bpy.types.DATA_PT_modifiers.remove(bevel_width_input_menu)

	del bpy.types.Scene.src_mat
	del bpy.types.Scene.trg_mat
	del bpy.types.Scene.checker_scale
	del bpy.types.Scene.texel_value
	del bpy.types.Scene.modifiersVisibilityStateAll	
	del bpy.types.Scene.copy_transform_offset
	del bpy.types.Scene.apply_uv_scale
	del bpy.types.Scene.json_materials_data_path
	del bpy.types.Scene.new_object_name_input
	del bpy.types.Scene.new_collection_name_input


