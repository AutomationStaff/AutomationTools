import bpy
import os
from bpy.utils import register_class, unregister_class
from bpy.types import Operator, Panel, Menu
import bmesh
import json
from mathutils import Vector, Matrix
from random import random, uniform
from . rigging_skinning import _class_method_mesh_, go_back_to_initial_mode


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
		if bpy.context.object.modifiers.active.type=='SHRINKWRAP':
			if mods_stack:			
				for m in mods_stack:				
					mod = m.type
					# find modifier
					if mod == 'SHRINKWRAP' and m.show_viewport:
						name = m.name
						o.modifier_copy(modifier= name)
						o.modifier_apply(modifier= obj.modifiers.active.name)

						# check result
						if name not in obj.modifiers[:]:
							self.report({'INFO'},  (name + " duplicated and applied"))
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
	# handy script for keyboard shortcuts
	bl_idname = "view3d.toggle_modifies_by_type"
	bl_label = "Toggle Modifiers By Type"
	bl_description = 'Toggle Modifiers by their type in Viewport'
	mod_type : bpy.props.StringProperty(name="type", default="SUBSURF")

	@classmethod
	def poll(cls, context):
		return context.object is not None

	def doToggleVisibilityActiveObject(self, t, mods_stack):
		# all other modifiers of that type will follow the visibility state of the first modifier's visibility in the stack
		
		if t and mods_stack:			
			# create the modifiers list of that type
			mods = []
			for m in mods_stack:
				mod = m.type
				if mod == t:
					mods.append(m)			
			
			if mods:
				# get the first modifier state
				first_mod_state = mods[0].show_viewport
								
				# turn on/off
				for m in mods:			
					m.show_viewport = not first_mod_state

					# if first_mod_state:
					# 	self.report({'INFO'}, (m.name + " OFF"))
					# else:										
					# 	self.report({'INFO'},  (m.name + " ON"))
				
				# return not first_mod_state

			else:
				self.report({'INFO'},  ((t.title()) + " not found"))
		else:
			self.report({'WARNING'}, "[Error]: Object has no Modifiers")

	def doToggleVisibilitySelectedObjects (self, t, mods_stack, state):		
		if t and mods_stack:
			# create the modifiers list of that type
			for m in mods_stack:
				mod = m.type
				if mod is not None and state is not None:
					if mod == t:
						# turn on/off
						m.show_viewport = state
			
		else:
			self.report({'WARNING'}, "[Error]: Object has no Modifiers")
	
	def execute(self, context):		
		t = self.mod_type
		sel = [obj for obj in bpy.context.selected_objects if obj.type == 'MESH']
		ao = bpy.context.object	
		state = False
		
		# active mesh
		if ao:			
			mods_stack = ao.modifiers[:]
			state = self.doToggleVisibilityActiveObject(t, mods_stack)

		# all other selected meshes
		if sel:
			for o in sel:
				if o != ao:
					mods_stack = o.modifiers[:]
					self.doToggleVisibilitySelectedObjects(t, mods_stack, state)			

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
		if len(bpy.context.selected_objects) > 1:
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
				if 	bevel.offset_type != 'WIDTH':
					bevel.offset_type = 'WIDTH'
				key_id = obj.data.shape_keys.key_blocks.id_data
				fcurve = obj.modifiers['Bevel'].driver_add('width')
				driver = fcurve.driver
				var = driver.variables.new()
				var.name = "var"
				var.type = "SINGLE_PROP"
				if val < 1:
					driver.expression =  "var * (1 - " + str(val) + ") + " + str(val)
				else:
					driver.expression =  "var * (" + str(val) + " - 1) + " + str(val)
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
	bl_description = "Apply active (Mirror/Shrinkwrap/Triangulate) modifier on the mesh with shape keys. Applying a geometric modifier such as Mirror leads to applying Shrinkwrap, Array, Bevel automatically."

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
		ks = bpy.context.object.active_shape_key		
		active_shape_key = bpy.context.object.active_shape_key.name	
		bpy.context.view_layer.objects.active = obj	
		indicies = get_faces_indicies(self, obj)
		if obj is not None:
			if obj.select_get() == False:
				obj.select_set(True)

			# if vertex count is not changed 
			vertex_count_change = ('MIRROR', 'ARRAY', 'BEVEL')
			vertex_count_nochange = ('TRIANGULATE', 'SHRINKWRAP', 'ARMATURE')

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
					#if armature
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
			else:
				self.report({'WARNING'},  "Only Mirror, Array, Bevel, Triangulate and Shrinkwrap modifiers can be applied!")
		
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
		if_sync_select = bpy.context.scene.tool_settings.use_uv_select_sync

		if bpy.context.active_object:                       
			bpy.context.area.type = 'IMAGE_EDITOR'

			bpy.ops.uv.unwrap(method='ANGLE_BASED', margin=0.001)
			bpy.context.area.ui_type = 'UV'

			if not if_sync_select:
				bpy.context.scene.tool_settings.use_uv_select_sync  = True				

			bpy.context.space_data.cursor_location[0] = self.U
			bpy.context.space_data.cursor_location[1] = self.V        

			bpy.ops.uv.snap_selected(target='CURSOR')
			
			bpy.context.area.type = 'VIEW_3D'			
			
			bpy.context.scene.tool_settings.use_uv_select_sync  = if_sync_select

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

class CreateUVs(Operator):
	bl_idname = "mesh.create_uvs_by_hard_edges"
	bl_label = "Create UVs"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = "Unwrap mesh(es)"

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
				bpy.ops.mesh.scale_uvs(command='SET')
			
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



class ScaleUVs(Operator):
	bl_label = "Scale Selected UVs"
	bl_idname = "mesh.scale_uvs"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = "Scale Selected UVs: 1 cm = 128x128 pix"
	command: bpy.props.StringProperty(options = {'HIDDEN'})
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
		for v in bm.verts:
			for loop in v.link_loops:		
				uv_data = loop[uv_layer]
				if uv_data.select and uv_data.pin_uv == False:
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
				for f in bm.faces:
					for loop in f.loops:		
						uv_data = loop[uv_layer]
						if uv_data.select:
							uv_face_list.append(loop.face)
			
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
				else:
					self.report({'WARNING'},  "Selection update is required. Select UVs manually in the UV Editor.")
			else:
				self.report({'WARNING'},  "UVMap not found!")

	def execute(self, context):		
		if_sync = False
		if bpy.context.scene.tool_settings.use_uv_select_sync:
			if_sync = True
			bpy.ops.uv.pin(clear=False)
			bpy.context.scene.tool_settings.use_uv_select_sync = False		
			bpy.ops.uv.select_pinned()			
			bpy.ops.uv.pin(clear=True)

		sel = bpy.context.selected_objects
		
		for obj in sel:
			if self.command == "SET":
				ratio_uvlayer = self.get_current_ratio(obj)
				if ratio_uvlayer is not None:
					current_ratio = ratio_uvlayer[0]
					texel = bpy.context.scene.texel_value
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
	angle_1 : bpy.props.FloatProperty(default = 0.5, min = 0.0, max = 3.14159 )
	angle_2 : bpy.props.FloatProperty(default = 1.5, min = 0.0, max = 3.14159)
	angle_3 : bpy.props.FloatProperty(default = 1.57, min = 0.0, max = 3.14159)

	@classmethod
	def poll(cls, context):
		return context.object is not None and context.mode == "EDIT_MESH"

	def execute(self, context):
		
		angle_1 = self.angle_1
		angle_2 = self.angle_2
		angle_3 = self.angle_3
		
		obj = bpy.context.object
		bm = bmesh.from_edit_mesh(obj.data)		
		
		verts = [v for v in bm.verts if v.select]
		#print (verts)
		bpy.ops.mesh.select_all(action='DESELECT')

		#find a 90deg angle between edges
		angles = {}
		for v in verts:
			edges = v.link_edges
			for e in edges:
				#e.select_set(True)
				#print (e.calc_face_angle())
				angles[e.index] = e.calc_face_angle(None)	
		#print (angles)

		#get non-90 deg edge for a seam
		for ind, ang in angles.items():
			if ang != None:
				if angle_1 < ang < angle_3:
					bm.edges.ensure_lookup_table()
					bm.edges[ind].select_set(True)
					break
		#get caps
		for ind, ang in angles.items():
			if ang != None:
				if ang > angle_2:
					bm.edges.ensure_lookup_table()
					bm.edges[ind].select_set(True)
					
		
		bpy.ops.mesh.mark_seam(clear=False)

		bm.select_flush_mode()
		bmesh.update_edit_mesh(obj.data)

		bm.select_mode = {"EDGE"}

		bpy.ops.mesh.loop_multi_select(ring=False)
		bpy.ops.mesh.mark_seam(clear=False)
		
		bm.select_mode = {"VERT"}
		for v in verts:
			v.select_set(True)
		
		bm.select_flush_mode()
		bmesh.update_edit_mesh(obj.data)		

		return {'FINISHED'}

class UnwrapPipe(Operator):
	bl_idname = "mesh.unwrap_pipe"
	bl_label = "Unwrap Pipe"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = "Unwrap Pipe"

	@classmethod
	def poll(cls, context):
		return context.object is not None and context.mode == "EDIT_MESH"

	def execute(self, context):		
		bpy.ops.mesh.select_all(action='DESELECT')
		obj = bpy.context.object
		bm = bmesh.from_edit_mesh(obj.data)
		
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
		bpy.ops.uv.unwrap(method='ANGLE_BASED', margin=0.001)	

		return {'FINISHED'}

class CreateUVChecker(Operator):
	bl_idname = "object.add_uv_checker"
	bl_label = "Unwrap Pipe"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = "Add UV Checker"

	@classmethod
	def poll(cls, context):
		return context.object is not None and context.object.active_material is not None

	def execute(self, context):
		checker_path = os.path.join(os.path.dirname(__file__),'images/checker_1.png')
		bpy.ops.image.open(filepath = checker_path)


		material = bpy.context.object.active_material
		if  material.use_nodes == False:
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

class FixMaterialName(Operator):
	bl_idname = "object.fix_material_name"
	bl_label = "Fix Material Name"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = "Fix material names by removing .00# endings"	
	symbol : bpy.props.StringProperty(name="Symbol")	

	@classmethod
	def poll(cls, context):
		return context.object is not None and len(bpy.context.object.material_slots) > 0		

	def fix_mat_names(self, context):
		if context and context.type == 'MESH' and len(context.material_slots) > 0:
			mat = context.active_material
			#materials number
			mat_list = context.data.materials
			mat_num = len(mat_list) - 1

			for i in mat_list:        
				#select material
				context.active_material_index = mat_num
				#get material name
				mat_name = context.active_material.name
				
				stuff = mat_name.rsplit(self.symbol, 1)
				mat_name = stuff[0]

				#assign material    
				if mat_name in bpy.data.materials:
					context.data.materials[mat_num] = bpy.data.materials[mat_name]
				else:
					context.data.materials[mat_num].name = mat_name

				mat_num -= 1

	def execute(self, context):

		sel = bpy.context.selected_objects
		if sel:
			for context in sel:
				bpy.context.view_layer.objects.active = context

				self.fix_mat_names(context)
		else:
			self.fix_mat_names(bpy.context.object)		

		return {'FINISHED'}


class FixMateriaSlots(Operator):
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
		with open(context.scene.json_mateials_data_path, 'r') as json_data:
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
					
					if len(sel) == 1:
						self.report({'INFO'}, str(difference) + " unused Slots have been deleted")
					else:
						self.report({'INFO'},  "Unused Slots have been deleted")
		else:
			self.report({'WARNING'},  "Nothing selected!")

		bpy.ops.object.select_all(action='DESELECT')
		for obj in sel:
			obj.select_set(True)	  
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
		return context.active_object is not None and bpy.context.object.type == "MESH"

	def execute(self, context): 
		mod = bpy.context.mode
		bm = bmesh.from_edit_mesh(bpy.context.object.data)
		sel = [f for f in bm.faces if f.select]
			
		if bpy.context.active_object:
			if bpy.context.object.type == "MESH":
				if bpy.context.mode == "OBJECT":
					bpy.ops.object.mode_set(mode = 'EDIT')

			bpy.ops.mesh.select_all(action='SELECT')            
			bpy.ops.mesh.normals_tools(mode="RESET")
			bpy.ops.mesh.select_all(action='DESELECT')

		bpy.ops.object.mode_set(mode = (mod.replace("_MESH", "")))

		# back to original selection
		for f in sel:
			f.select_set(True)

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

class GenerateHierarchy(Operator):
	bl_label = 'Generate Hierarchy'
	bl_idname = 'object.generate_hierarchy'
	bl_description = 'Generate Collections for Car Parts'
	type: bpy.props.StringProperty(options={'HIDDEN'})
	
	@classmethod
	def poll(cls, context):
		return context.collection is not None         
		
	def execute(self, context):
		collection = context.collection
		if self.type == 'Body':
			list = ('Body Variants [Select for Batch Export]', 'New Body [Strictly 1 Body, 1 Bounds mesh]')
			generate_collections(self, context, list, 0, 1)

		elif self.type == 'Rim':
			list = ('Rim Variants [Select for Batch Export]', 'New Rim [Any Rim mesh(es)]')
			generate_collections(self, context, list, 0, 1)
		
		elif self.type == 'Fixture':
			list = ('Fixture Variants [Select for Batch Export]', 'New Fixture [Select for Single Export]', '_Conforming_Mesh', '_Skinned_Mesh', '_UV_Mesh')
			generate_collections(self, context, list, 1, 3)

		return {'FINISHED'}

class CurveBetween2Objects (Operator):
	bl_idname = "object.curve_between_2_objects"
	bl_label = "Curve Between 2 Objects"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = "Create Curve placed between selected Objects"	

	@classmethod
	def poll(cls, context):
		return context.object is not None and context.mode == 'OBJECT' or context.mode == 'EDIT_MESH'
	
	def get_selected_verts_number(self):
		bpy.context.object.data.update()
		two_selected = [v for o in bpy.context.selected_objects for v in o.data.vertices if v.select]
		if len(two_selected) == 2:
			return True
		else:
			return False
	
	def getEmptyPositions(self):		
		positions = []
		if len(bpy.context.selected_objects) <= 2 and bpy.context.mode == 'EDIT_MESH' and self.get_selected_verts_number() == True:
			bpy.ops.object.mode_set(mode = 'OBJECT')
			bpy.ops.object.mode_set(mode = 'EDIT')
			# if vertex selection
			if bpy.context.scene.tool_settings.mesh_select_mode[0] == True and bpy.context.active_object.type == 'MESH':		
				# reset selection
				bpy.ops.mesh.reset_vertex_selection()
				bpy.context.scene.tool_settings.transform_pivot_point = 'BOUNDING_BOX_CENTER'
				bpy.context.object.data.update()
			
				# create 2 locators to get their coordinates
				bpy.ops.object.v_locators()		
			
				sel = bpy.context.selected_objects
				if sel:
					if len(sel) > 1:						
						for i in sel:
							if i.type == 'EMPTY':
								positions.append(i.location)
						return positions
					else:
						return None
			
		elif bpy.context.selected_objects and len(bpy.context.selected_objects) == 2 and bpy.context.mode == 'OBJECT':
			for i in bpy.context.selected_objects:
				positions.append(i.location)
			return positions


	def MakePolyLine(self, objname, cList, weight):
			
		curvedata = bpy.data.curves.new(name="curve_2_points", type='CURVE')
		curvedata.dimensions = '3D'

		objectdata = bpy.data.objects.new(objname, curvedata)
		objectdata.location = (0,0,0) #object origin
		bpy.context.scene.collection.objects.link(objectdata)	

		polyline = curvedata.splines.new('POLY')
		polyline.points.add(len(cList)-1)
		for num in range(len(cList)):
			x, y, z = cList[num]
			polyline.points[num].co = (x, y, z, weight)

		return polyline
		
	def execute(self, context):
		#update selection
		if bpy.context.object.type != "EMPTY":
			if bpy.context.mode == 'OBJECT':			
				bpy.ops.object.mode_set(mode = 'EDIT')
				bpy.ops.object.mode_set(mode = 'OBJECT')

			elif bpy.context.mode == 'EDIT_MESH':
				bpy.ops.object.mode_set(mode = 'OBJECT')
				bpy.ops.object.mode_set(mode = 'EDIT')

		if self.getEmptyPositions() is not None:
			# if edit mode
			if bpy.context.object.type == "MESH":
				if bpy.context.mode == "EDIT_MESH":
					bpy.ops.object.mode_set(mode = 'OBJECT')

			# get curve name
			name = bpy.context.scene.curve_name
			if name:
				if name in bpy.context.scene.objects:
					while name in bpy.context.scene.objects:					
						lastNum = int(name[-1])
						name = name[:-1]
						name = name + str(lastNum + 1)
			# create line
				if bpy.context.scene.curve_type == 'Line':					
					if bpy.context.mode == 'OBJECT':
						listOfVectors = self.getEmptyPositions()
						if listOfVectors is not None:
							self.MakePolyLine(name, listOfVectors, 0.01)						
							bpy.ops.object.select_all(action = 'DESELECT')
							
							bpy.data.objects[name].select_set(True)
							bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
							bpy.context.view_layer.objects.active  = bpy.data.objects[name]
						
			# create bezier
				if bpy.context.scene.curve_type == 'Bezier':
					if bpy.context.mode == 'OBJECT':
						listOfVectors = self.getEmptyPositions()
						if listOfVectors is not None:
							self.MakePolyLine(name, listOfVectors, 0.01)
							
							bpy.ops.object.select_all(action = 'DESELECT')
							bpy.data.objects[name].select_set(True)
							bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
							bpy.context.view_layer.objects.active  = bpy.data.objects[name]

							bpy.ops.object.mode_set(mode = 'EDIT')
							bpy.ops.curve.select_all(action='SELECT')
							bpy.ops.curve.spline_type_set(type='BEZIER')
							bpy.ops.curve.handle_type_set(type='AUTOMATIC')
							bpy.ops.object.mode_set(mode = 'OBJECT')

				#assign color
				bpy.context.object.color = (0, 0, 1, 1)

				# cleanup
				data = bpy.data.objects
				for o in data:
					if 'VertexEmpty' in o.name:		
						data.remove(o, do_unlink=True)						
			else:
				self.report({'WARNING'},  "Curve is not named")
		else:
			self.report({'WARNING'},  "Select 2 objects or 2 vertices!")

		return {'FINISHED'}

class EdgeToCurve(Operator):
	bl_idname = "object.edge_to_curve"
	bl_label = "Edges to Curve"
	bl_description = "Convert Edges to Curve"
	bl_options = {'REGISTER', 'UNDO'}

	@classmethod
	def poll(cls, context):
		return bpy.context.active_object
	
	def execute(self, context):
		o = bpy.ops.object
		m = bpy.ops.mesh
		obj = bpy.context.active_object
		
		# reset selection
		bpy.ops.mesh.reset_vertex_selection()					
		m.select_mode(type="EDGE")
		bpy.context.scene.tool_settings.transform_pivot_point = 'BOUNDING_BOX_CENTER'

		# get selected edges
		edges = [v for v in obj.data.edges if v.select]		
		
		if len(edges):			
			if bpy.context.scene.curve_type == 'Bezier':		
				# detach edges			
				bpy.ops.mesh.duplicate_detach_faces()

				# if modifiers
				if len(obj.modifiers[:]):
					for m in obj.modifiers[:]:
						bpy.ops.object.modifier_remove(modifier=m.name)

				# make conversion
				bpy.ops.object.convert(target='CURVE')
				bpy.ops.object.mode_set(mode = 'EDIT')
				bpy.ops.curve.select_all(action='SELECT')
				bpy.ops.curve.spline_type_set(type='BEZIER')
				bpy.ops.curve.handle_type_set(type='AUTOMATIC')
				bpy.ops.curve.smooth()
				bpy.ops.curve.smooth()

				#assign color
				bpy.context.object.color = (1, 0, 0, 1)

				bpy.ops.curve.select_all(action='DESELECT')
				bpy.ops.object.mode_set(mode = 'OBJECT')

			elif bpy.context.scene.curve_type == 'Line':
				bpy.ops.mesh.duplicate_detach_faces()
				bpy.ops.object.mode_set(mode = 'OBJECT')

		else:
			self.report({'WARNING'},  "Nothing selected")

		return {'FINISHED'}

class VertexPaintrFill(Operator):
	bl_idname = "mesh.fill_vertex_color"
	bl_label = "Fill Vertex Color"
	bl_description = "Fill Vertex Color"
	bl_options = {'REGISTER', 'UNDO'}
	color_new: bpy.props.StringProperty(options = {'HIDDEN'})
	
	@classmethod
	def poll(cls, context):
		return context.active_object and context.mode == 'EDIT_MESH'

	def _fill_polygon_(self, obj, replace_with):
		obj.use_paint_mask = True
		if bpy.context.tool_settings.vertex_paint.brush != bpy.data.brushes['Draw']:
			bpy.context.tool_settings.vertex_paint.brush = bpy.data.brushes['Draw']
		bpy.data.brushes['Draw'].color = replace_with[:3]
		bpy.ops.paint.vertex_color_set()

	
	def replace_vertex_color(self, context):
		sel = [obj for obj in bpy.context.selected_objects if obj.type != "EMPTY"]
		mode = bpy.context.mode
		if len(sel) > 0:
			for o in sel:
				bpy.context.view_layer.objects.active = o
				obj = o.data
				bpy.ops.object.mode_set(mode = 'VERTEX_PAINT')

				if_replace = bpy.context.scene.replace_vertex_paint_value
				fill_polygon = bpy.context.scene.fill_vertex_paint
				alpha_value = bpy.context.scene.vertex_color_alpha_value
				replace = bpy.context.scene.color_replace

				if if_replace and fill_polygon:
					bpy.context.scene.fill_vertex_paint = False
					fill_polygon = bpy.context.scene.fill_vertex_paint

				replace_with = None
				if self.color_new == "Red":
					replace_with = (1.0, 0.0, 0.0, 0.0)
				elif self.color_new == "Green":
					replace_with = (0.0, 1.0, 0.0, 0.0)
				elif self.color_new == "Blue":
					replace_with = (0.0, 0.0, 1.0, 0.0)
				elif self.color_new == "A":
					replace_with = (0.0, 0.0, 0.0, alpha_value)
				elif self.color_new == "White":
					replace_with = (1.0, 1.0, 1.0, 0.0)
				elif self.color_new == "Black":
					replace_with = (0.0, 0.0, 0.0, 0.0)

				to_replace = None
				if replace == 'R':
					to_replace = (1.0, 0.0, 0.0)
				elif replace == 'G':
					to_replace = (0.0, 1.0, 0.0)
				elif replace == 'B':
					to_replace = (0.0, 0.0, 1.0)
				elif replace == 'White':
					to_replace = (1.0, 1.0, 1.0)
				elif replace == 'Black':
					to_replace = (0.0, 0.0, 0.0)
					
				if if_replace == False:
					verts = [v for v in obj.vertices if v.select]
				else:
					verts = [v for v in obj.vertices]
				
				if if_replace:
					if fill_polygon is False:
						for polygon in obj.polygons:
							for v in verts:
								for i, index in enumerate(polygon.vertices):
									if v.index == index:
										loop_index = polygon.loop_indices[i]
										# paint
										if obj.vertex_colors.active.data[loop_index].color[:3] == to_replace:
											obj.vertex_colors.active.data[loop_index].color = replace_with
										else:
											# clamp and paint
											for s in range(4):
												obj.vertex_colors.active.data[loop_index].color[s] = round(obj.vertex_colors.active.data[loop_index].color[s], 0)
											if to_replace is not None:
												if obj.vertex_colors.active.data[loop_index].color[:3] == to_replace:
													obj.vertex_colors.active.data[loop_index].color = replace_with
											else:
												obj.vertex_colors.active.data[loop_index].color = replace_with

					else:
						self._fill_polygon_(obj, replace_with)
				else:
					# alpha
					if fill_polygon is False:
						for polygon in obj.polygons:
							for v in verts:
								for i, index in enumerate(polygon.vertices):
									if v.index == index:
										loop_index = polygon.loop_indices[i]
										if self.color_new != "A":
											obj.vertex_colors.active.data[loop_index].color = replace_with
										else:
											obj.vertex_colors.active.data[loop_index].color[3] = alpha_value
					else:
						self._fill_polygon_(obj, replace_with)

				bpy.ops.object.mode_set(mode = 'EDIT')
				bpy.ops.mesh.select_all(action='DESELECT')
		else:
			self.report({'WARNING'},  "Active object is hidden or not found!")
		go_back_to_initial_mode(self, mode)

	def execute(self, context):	
		self.replace_vertex_color(context)
		return {'FINISHED'}

class VertexColorChannelOnOff(Operator):
	bl_idname = "mesh.channel_on_off"
	bl_label = "Channel On/Off"
	bl_description = "Channel On/Off"
	bl_options = {'REGISTER', 'UNDO'}
	action: bpy.props.FloatProperty(options = {'HIDDEN'})
	
	@classmethod
	def poll(cls, context):
		return context.active_object and context.mode == 'EDIT_MESH'		

	def execute(self, context):		
		sel = [obj for obj in bpy.context.selected_objects if obj.type != "EMPTY"]
		mode = bpy.context.mode
		if len(sel) > 0:
			for o in sel:
				bpy.context.view_layer.objects.active = o
				obj = o.data
				bpy.ops.object.mode_set(mode = 'VERTEX_PAINT')

				if_replace = bpy.context.scene.replace_vertex_paint_value
				fill_polygon = bpy.context.scene.fill_vertex_paint
				alpha_value = bpy.context.scene.vertex_color_alpha_value
				replace = bpy.context.scene.color_replace

				if if_replace and fill_polygon:
					bpy.context.scene.fill_vertex_paint = False
					fill_polygon = bpy.context.scene.fill_vertex_paint
				

				to_replace = None

				if replace == 'R':
					to_replace = 0

				elif replace == 'G':
					to_replace = 1

				elif replace == 'B':
					to_replace = 2
					
				if if_replace == False:
					verts = [v for v in obj.vertices if v.select]
				else:
					verts = [v for v in obj.vertices]
				
				if if_replace:
					if fill_polygon is False:
						for polygon in obj.polygons:
							for v in verts:
								for i, index in enumerate(polygon.vertices):
									if v.index == index:
										loop_index = polygon.loop_indices[i]
										#zero out channel
										if to_replace is not None:
											r = obj.vertex_colors.active.data[loop_index].color[0]
											g = obj.vertex_colors.active.data[loop_index].color[1]
											b = obj.vertex_colors.active.data[loop_index].color[2]

											obj.vertex_colors.active.data[loop_index].color[to_replace] =  self.action		


					else:
						self._fill_polygon_(obj, replace_with)
				else:
					# alpha
					if fill_polygon is False:
						for polygon in obj.polygons:
							for v in verts:
								for i, index in enumerate(polygon.vertices):
									if v.index == index:
										loop_index = polygon.loop_indices[i]
										if self.color_new != "A":
											obj.vertex_colors.active.data[loop_index].color = replace_with
										else:
											obj.vertex_colors.active.data[loop_index].color[3] = alpha_value
					else:
						self._fill_polygon_(obj, replace_with)

				bpy.ops.object.mode_set(mode = 'EDIT')
				bpy.ops.mesh.select_all(action='DESELECT')
		else:
			self.report({'WARNING'},  "Nothing changed!")
		go_back_to_initial_mode(self, mode)
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
		obj = bpy.context.active_object        
		if obj is not None:
			bpy.context.window_manager.clipboard = obj.name 
		else:
			self.report({'WARNING'},  "Incorrect source object!")
		
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
				i.name = bpy.context.window_manager.clipboard
		
		return {'FINISHED'}

class NameForBake(Operator):
	# select 2 meshes and call the command. Highest will get suffix/name "_high", lowest "_low"
	bl_idname = "object.rename_lp_hp"
	bl_label = "Name For Bake"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = "Add *_lp and *_hp in the ends of high/low poly meshes. Select 2 meshes and run the script"

	@classmethod
	def poll(cls, context):
		return context.object is not None
	
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
		   
		#select the collection where the active object is located
		bpy.ops.object.select_act_obj_collection()        

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

			new_empty.name = i.name
		
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
	bl_label = "Move to Scene Center"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = "Move to Scene Centre"

	@classmethod
	def poll(cls, context):
		return context.object is not None

	def execute(self, context):		
		sel = bpy.context.selected_objects		
		if len(sel):
			for i in sel:
				if i.data.users == 1:
					i.location = (0,0,0)
				else:
					self.report({'WARNING'},  "Nothing changed. The object has instances")
		
		return {'FINISHED'}

class SocketInVertexSelectionCentre(Operator):    
	bl_idname = "mesh.socket_in_vertex_selection_centre"
	bl_label = "Socket In Vertex Selection Centre"
	bl_description = "Create a Socket in the vertex selection centre"
	
	@classmethod
	def poll(cls, context):
		return context.area.type == "VIEW_3D" and context.mode == "EDIT_MESH" and context.object.type == "MESH"
	
	def execute(self, context):
		obj = bpy.context.object
		bm = bmesh.from_edit_mesh(obj.data)        
		
		verts = []
		v_pos = Vector()        

		for vert in bm.verts:
			if vert.select == True:
				verts.append(vert)

		if len(verts) > 0:
			for vert in verts:
				v_pos += vert.co            

			v_pos_avg = v_pos / len(verts)
			orient = bpy.context.scene.transform_orientation_slots[0].type            

			new_socket = bpy.data.objects.new("SOCKET_", None)
			scene_collection = context.layer_collection.collection
			scene_collection.objects.link(new_socket)
			
			if orient == "LOCAL":
				new_matrix = obj.matrix_world @ Matrix.Translation(v_pos_avg)
				new_socket.matrix_world = new_matrix                
				
			elif orient == "GLOBAL":
				new_matrix = obj.matrix_world @ Matrix.Translation(v_pos_avg)
				new_socket.matrix_world = new_matrix
				new_socket.rotation_euler = ( 0, 0, 0 )

			bpy.context.view_layer.objects.active = obj          
			obj.select_set(True)
			bpy.ops.mesh.select_all(action='DESELECT')             
		else:
			self.report({'WARNING'}, self.bl_idname + ": "+ "Nothing selected!")
			
		return {'FINISHED'}

class SocketInObjectPivotPosition(Operator):
	bl_idname = "object.socket_in_pivot"
	bl_label = "Socket in Object Pivot"
	bl_description = "Create Sockets in the objects' pivot positions"

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
				bpy.ops.object.empty_add(type='PLAIN_AXES', radius=0.5, location = (pos))
				bpy.context.active_object.name = 'SOCKET_'
		else:
			self.report({'WARNING'}, self.bl_idname + ": " + "Nothing selected!")

		return {'FINISHED'}

# Functions
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
		bpy.ops.object.mode_set(mode = 'OBJECT')

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

addon_keymaps = []

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
	CurveBetween2Objects,
	EdgeToCurve,
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
	VertexPaintrFill,
	CopyObjectName,
	PasteObjectName,
	NameForBake,
	CreateGroup,
	MoveToSceneCenter,
	SocketInVertexSelectionCentre,
	SocketInObjectPivotPosition,
	CreateUVs,
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
	VertexColorChannelOnOff,
	FixMateriaSlots,
	SnapUVBottomsUVs
)

# Register
def register():
	for cls in classes:
		bpy.utils.register_class(cls)

	bpy.types.Scene.src_mat = bpy.props.StringProperty()
	bpy.types.Scene.trg_mat = bpy.props.StringProperty()

	bpy.types.Scene.checker_scale = bpy.props.FloatProperty(description = 'Scale Checker Texture. Textured Mode only', default = 1.0, min = 1.0, max = 10.0, update = scale_uv_checker)
	bpy.types.Scene.texel_value = bpy.props.FloatProperty(description = 'UV size value. Default Automation UV size is 50, which is 1x1 scene unit = 128x128 px texture', default = 50.0)

	bpy.types.Scene.replace_vertex_paint_value = bpy.props.BoolProperty(description = 'Replace Vertex Color Mode')
	bpy.types.Scene.fill_vertex_paint = bpy.props.BoolProperty(description = 'Fill Polygons. Fill Vertices is default')

	bpy.types.Scene.color_replace = bpy.props.EnumProperty(
	name="",
	description="Select color to replace",
	items=[('R', 'R', ''), ('G', 'G', ''), ('B', 'B', ''), ('White', 'White', ''), ('Black', 'Black', ''), ('All', 'All', '')]
	)

	bpy.types.Scene.vertex_color_alpha_value = bpy.props.FloatProperty(name = '', soft_min = 0, soft_max = 1, description = 'Vertex color alpha value')
	bpy.types.Scene.modifiersVisibilityStateAll = bpy.props.BoolProperty()	
	
	keymaps_list = (
	'DATA_TRANSFER',
	'MESH_CACHE',
	'MESH_SEQUENCE_CACHE',
	'NORMAL_EDIT',
	'WEIGHTED_NORMAL',
	'UV_PROJECT',
	'UV_WARP',
	'VERTEX_WEIGHT_EDIT', 
	'VERTEX_WEIGHT_MIX',
	'VERTEX_WEIGHT_PROXIMITY',
	'ARRAY',
	'BEVEL',
	'BOOLEAN',
	'BUILD',
	'DECIMATE',
	'EDGE_SPLIT',
	'NODES',
	'MASK',
	'MIRROR',
	'MESH_TO_VOLUME',
	'MULTIRES',
	'REMESH',
	'SCREW',
	'SKIN',
	'SOLIDIFY',
	'SUBSURF',
	'TRIANGULATE',
	'VOLUME_TO_MESH',
	'WELD',
	'WIREFRAME',
	'ARMATURE',
	'CAST',
	'CURVE',
	'DISPLACE',
	'HOOK',
	'LAPLACIANDEFORM',
	'LATTICE',
	'MESH_DEFORM',
	'SHRINKWRAP', 
	'SIMPLE_DEFORM', 
	'SMOOTH',
	'CORRECTIVE_SMOOTH',
	'LAPLACIANSMOOTH',
	'SURFACE_DEFORM', 
	'WARP',
	'WAVE',
	'VOLUME_DISPLACE',
	'CLOTH', 
	'COLLISION',
	'DYNAMIC_PAINT', 
	'EXPLODE',
	'FLUID', 
	'OCEAN',
	'PARTICLE_INSTANCE',
	'PARTICLE_SYSTEM',
	'SOFT_BODY',
	'SURFACE'
	)
	
	km = bpy.context.window_manager.keyconfigs.addon.keymaps.new(name="3D View", space_type='VIEW_3D')
	
	assigned = {
	'MIRROR':'ONE',
	'BEVEL':'TWO',
	'SUBSURF':'THREE',
	'SOLIDIFY':'FOUR',
	'SHRINKWRAP':'FIVE',
	'CURVE':'SIX',
	'BOOLEAN':'SEVEN',
	'TRIANGULATE':'EIGHT',
	'LATTICE':'NINE'
   }	
	
	for item in keymaps_list:
		if item in assigned:
			key = km.keymap_items.new("view3d.toggle_modifies_by_type", assigned[item], 'PRESS')
			key.active = True
			key.properties.mod_type=item		
			addon_keymaps.append((km, key))
		else:
			key = km.keymap_items.new("view3d.toggle_modifies_by_type", 'NONE', 'PRESS')
			key.active = False
			key.properties.mod_type=item		
			addon_keymaps.append((km, key))	

	#add buttons to Properties > Modifiers
	bpy.types.DATA_PT_modifiers.append(bevel_width_input_menu)

	bpy.types.Scene.curve_name = bpy.props.StringProperty(name='Name', default='Curve_1')

	bpy.types.Scene.curve_type = bpy.props.EnumProperty(
	name="",
	description="",
	items=[('Bezier', 'Bezier', ''), ('Line', 'Line', '')]
	)
	
	bpy.types.Scene.json_mateials_data_path = bpy.props.StringProperty(
		name="",
		subtype='FILE_PATH',
		description = 'UE materials data File Path'
	)
	

# Unregister
def unregister():
	for cls in reversed(classes):
		bpy.utils.unregister_class(cls)

	bpy.types.Scene.src_mat
	bpy.types.Scene.trg_mat
	bpy.types.Scene.checker_scale
	bpy.types.Scene.texel_value
	bpy.types.Scene.color_replace
	bpy.types.Scene.vertex_color_alpha_value
	bpy.types.Scene.fill_vertex_paint
	bpy.types.Scene.replace_vertex_paint_value
	bpy.types.Scene.modifiersVisibilityStateAll
	
	for km, kmi in addon_keymaps:
		km.keymap_items.remove(kmi)
	addon_keymaps.clear()
	
	bpy.types.DATA_PT_modifiers.remove(bevel_width_input_menu)

	bpy.types.Scene.curve_name
	bpy.types.Scene.curve_type
	bpy.types.Scene.json_mateials_data_path
	




