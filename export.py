import bpy
import bmesh
from bpy.utils import register_class, unregister_class
from bpy.types import Operator
from pathlib import Path
from mathutils import Vector
import os
import copy
from stat import *
from . import modeling
from math import isclose

class StandardBatchExport(Operator):
	bl_idname = "object.standard_batch_export"
	bl_label = "Standard Batch Export"
	bl_description = "Standard Automation Batch Exporter. Requires object selection. Exports Mesh, Armature, Empty object types. Exported files are named as the scene meshes. Note that it does not fix mirrored triangulation"

	@classmethod
	def poll(cls, context):
		return context.object is not None

	# main export function
	def exp(self, obj_name, file_path, apply_transform):
		bpy.ops.export_scene.fbx(
		filepath=(file_path + "/" + obj_name + ".fbx"),
		check_existing=False,
		use_selection=True,
		object_types={'EMPTY','ARMATURE','MESH'},
		bake_anim=False,
		axis_forward='Y',
		axis_up='Z',
		add_leaf_bones=False,
		use_custom_props=True,
		mesh_smooth_type='EDGE',
		bake_space_transform=apply_transform
	   )

	def execute(self, context):
		bpy.ops.view3d.remove_duplicated_items(collection=0)

		file_path = bpy.context.scene.export_path
		if_apply_transform=bpy.context.scene.if_apply_transform

		forced_object_mode(self, context, context.object)

		# if directory exists
		if  os.path.exists(file_path):
			o = bpy.ops.object
			ao = bpy.context.active_object
			d = bpy.data
			c = bpy.context
			sel = bpy.context.selected_objects
			sel_return = bpy.context.selected_objects

			sel = bpy.context.selected_objects[:]
			if sel:
				if c.object.type == "MESH" and c.active_object.mode == 'OBJECT':
					sel = bpy.context.selected_objects[:]
					o.select_all(action='DESELECT')

					obj_copy = None

					for obj in sel:
						if obj.data.shape_keys and len(obj.modifiers):					
							obj_copy = bpy.data.objects.new(obj.name, obj.data.copy())
							context.scene.collection.objects.link(obj_copy)
							obj_copy.select_set(True)
							context.view_layer.objects.active = obj					
							bpy.ops.object.modifiers_copy_to_selected()
							obj_copy.modifiers.active = obj_copy.modifiers[0]
							
							obj.select_set(False)								
							context.view_layer.objects.active = obj_copy

							apply_shape_keys_poll = True
							for mod in obj_copy.modifiers:
								if mod.type not in {'MIRROR', 'ARRAY', 'BEVEL', 'TRIANGULATE', 'SHRINKWRAP', 'ARMATURE', 'WEIGHTED_NORMAL', 'NODES'}:
									self.report({'WARNING'},  obj.name + ' skipped because it has unsupported for applying modifier of type ' + mod.type + ' !')				
									apply_shape_keys_poll = False
									break

							obj = obj_copy
							
							if apply_shape_keys_poll:
								while len(obj_copy.modifiers) > 0:									
									bpy.ops.object.apply_modifiers_with_shape_keys()																		
							else:
								continue											
						
						obj.select_set(True)
						context.view_layer.objects.active = obj						
						
						if obj.type == "MESH":
							obj.select_set(True)
							# sockets
							if obj.children:
								bpy.ops.object.select_grouped(type='CHILDREN')
								ch = bpy.context.selected_objects
								for n in ch:
									if bpy.context.object.type == 'EMPTY':
										n.select_set(True)
								d.objects[obj.name].select_set(True)
								bpy.context.view_layer.objects.active = d.objects[obj.name]
							# armature
							obj_armature = get_armature(self, obj)
							if obj_armature is not None:
								obj_armature.object.select_set(True)

						# file full name
						file = file_path + obj.name + ".fbx"

						# check file writing permissions
						if os.access(file, os.W_OK) or os.access(file, os.F_OK):
							os.chmod(file, 0o744)

						# property 'offset_x' used when engine part segments like boxer front sump should have X-offset in Unreal
						if 'offset_x' in obj:
							bpy.ops.transform.translate(value=(obj['offset_x'], 0, 0))
						
						location = Vector()
						if context.scene.if_move_to_origin:
							location = Vector((obj.location))
							obj.location = (0.0, 0.0, 0.0)

						# export
						self.exp(validate_export_name(self, obj.name), file_path, if_apply_transform)

						if context.scene.if_move_to_origin:
							obj.location = location

						if 'offset_x' in obj:
							bpy.ops.transform.translate(value=(-(obj['offset_x']), 0, 0))

						self.report({'INFO'},  file_path + validate_export_name(self, obj.name) + ".fbx")
						o.select_all(action='DESELECT')

						if obj_copy is not None:
							bpy.data.objects.remove(obj_copy, do_unlink=True)

					# Back to original selection
					o.select_all(action='DESELECT')
					for obj in sel_return:
							obj.select_set(True)
					bpy.context.view_layer.objects.active = ao
			else:
				self.report({'WARNING'}, "Nothing selected")
		else:
			self.report({'WARNING'}, 'The directory is not valid! Try selecting it again with Relative Path unchecked in the Blender file dialog settings.')
		return {'FINISHED'}

class BodyExport(Operator):
	bl_idname = "object.body_export"
	bl_label = "Body Export"
	bl_description = "Export Car Body with its Boundboxes located inside their own collection named as a future fbx file. Select the body collection in Outliner ant press [Export Single]. Armature should be in the root Scene Collection only"
	bl_options = {'REGISTER', 'UNDO'}

	@classmethod
	def poll(cls, context):
		return context.collection is not None

	# export function
	def exp(self, name, file_path, apply_transform):
		bpy.ops.export_scene.fbx(
		filepath=(file_path + "/" + name + ".fbx"),
		use_active_collection=True,
		check_existing=False,
		use_selection=False,
		object_types={'ARMATURE','MESH'},
		bake_anim=False,
		global_scale=1.0,
		axis_forward='Y',
		axis_up='Z',
		primary_bone_axis='Y',
		secondary_bone_axis='X',
		add_leaf_bones=False,
		apply_unit_scale=True,
		mesh_smooth_type='EDGE',
		use_tspace=False,
		use_mesh_modifiers=False,
		bake_space_transform=apply_transform
		)

	def get_body_and_bounds(self, content):
		if len(content) == 2:
			meshes = {'body': None, 'bounds': None}
			if len(content[0].data.vertices) > len(content[1].data.vertices) and len(content[0].data.vertices) != len(content[1].data.vertices):
				meshes['body']=content[0]
				meshes['bounds']=content[1]
			else:
				meshes['body']=content[1]
				meshes['bounds']=content[0]

		if len(meshes):
			return meshes
		else:
			return None

	def content_validation(self, content):
		for	o in content:
			if o.type != 'MESH':
				return False
		return True

	def content_forced_unhide(self, mesh):
		state = {'hide_viewport': True, 'hide_get': True, 'hide_select': True}
		if mesh.hide_viewport:
			mesh.hide_viewport = False
			state['hide_viewport'] = False
		if mesh.hide_get():
			mesh.hide_set(False)
			state['hide_get'] = False
		if mesh.hide_select:
			mesh.hide_select = False
			state['hide_select'] = False
		return state

	def execute(self, context):
		file_path = bpy.context.scene.export_path
		ops = bpy.ops.object
		obj = bpy.context.object
		if_apply_transform = bpy.context.scene.if_apply_transform

		forced_object_mode(self, context, context.object)
		# if directory exists
		if  os.path.exists(file_path):
			collection = bpy.context.collection
			name = collection.name

			full_name = file_path + validate_export_name(self, name) + '.fbx'

			if collection.name != 'Master Collection':
				#get collection's content
				content = bpy.context.collection.all_objects[:]
				if content:
					if self.content_validation(content):
						if len(content) == 2:
							# get body
							body_and_bounds = self.get_body_and_bounds(content)
							body = body_and_bounds['body']
							bounds = body_and_bounds['bounds']

							if body and bounds:
								#unhide the body and bounds if hidden
								body_viewport_state = self.content_forced_unhide(body)
								bounds_viewport_state = self.content_forced_unhide(bounds)

								# if boundboxes have UVMaps
								if len(bounds.data.uv_layers[:]) != 0:
									bpy.context.view_layer.objects.active = bounds
									for uvmap in bounds.data.uv_layers[:]:
										bpy.ops.mesh.uv_texture_remove()
									bpy.context.view_layer.objects.active = None

								#initialize a copy
								body_copy = None

								if bpy.context.scene.if_apply_modifiers:
									bpy.ops.object.select_all(action='DESELECT')
									body.select_set(True)

									# make sure Base is active shape key
									if body.data.shape_keys:
										body.active_shape_key_index = 0
										keys = body.data.shape_keys.key_blocks[:]
										for i in keys:
											if i.name != 'Basis':
												if i.value != 0:
													i.value = 0

									bpy.context.view_layer.objects.active = body
									bpy.ops.object.duplicate()
									body.select_set(False)
									collection.objects.unlink(body)
									body_copy = bpy.context.view_layer.objects.active

									# check body UVMaps count
									if len(body_copy.data.uv_layers[:]) == 0:
										self.report({'WARNING'}, self.bl_label + ": " + "Body does not have UVMaps!")

									elif 0 < len(body_copy.data.uv_layers[:]) < 2:
										body_copy.data.uv_layers.new(name='UVMap', do_init=True)

									#apply modifiers Mirror first
									if body_copy:
										indices = get_faces_indices(self, body_copy)
										if body_copy.modifiers:
											# if mirror
											if 'Mirror' in body_copy.modifiers:
												body_copy.modifiers.active = body_copy.modifiers['Mirror']
												if_shape_keys(self, body_copy, 'Mirror', indices)

											# if no mirror
											elif 'Mirror' not in body_copy.modifiers and 'Triangulate' in body_copy.modifiers:
												body_copy.modifiers.active = body_copy.modifiers['Triangulate']
												if_shape_keys(self, body_copy, 'Triangulate', indices)

											# apply the rest
											if body_copy.modifiers:
												if body_copy.data.shape_keys:
													i = 0
													for m in body_copy.modifiers:
														if m.type != 'ARMATURE':
															body_copy.modifiers.active = body_copy.modifiers[i]
															bpy.ops.object.apply_modifiers_with_shape_keys()
															i += 1
												else:
													for m in body_copy.modifiers:
														if m.type != 'ARMATURE':
															ops.modifier_apply(modifier = m.name)

								armature = None
								# add armature to the collection
								if "Armature" in body_copy.modifiers:
									armature = body_copy.modifiers['Armature'].object
									if armature.name not in collection.all_objects:
										armature.select_set(True)
										collection.objects.link(armature)
								# check the export flag
								if bpy.context.scene.export_flag:
									if name:
										if file_path:
											if os.access(full_name, os.W_OK) or os.access(full_name, os.F_OK):
												os.chmod(full_name, 0o744)
											if bpy.context.scene.debug_mode == False:
												self.exp(validate_export_name(self, name), file_path, if_apply_transform)
												self.report({'INFO'}, full_name)
										else:
											self.report({'WARNING'}, 'File path is not valid!')
									else:
										self.report({'WARNING'}, 'Active collection is not found!')
								else:
									self.report({'WARNING'},  "Export Failed! Unequal vertex count of shape keys. Find the debugging details in the console window")
									bpy.context.scene.export_flag = True

								# cleanup
								if armature:
									if armature.name in collection.all_objects:
										collection.objects.unlink(armature)
										armature.select_set(False)

								if body_copy:
									if body_copy.name in collection.all_objects:
										bpy.ops.object.select_all(action='DESELECT')
										body_copy.select_set(True)
									if bpy.context.scene.debug_mode == False:
										bpy.ops.object.delete(use_global=True, confirm=False)
									else:
										body_copy.name = body.name + "_debug"

								if body:
									if body.name not in collection.all_objects:
										collection.objects.link(body)
										bpy.context.view_layer.objects.active = body

								#if body hidden/locked
								if body_viewport_state['hide_viewport'] == False:
									body.hide_viewport = True
								if body_viewport_state['hide_get'] == False:
									body.hide_set(True)
								if body_viewport_state['hide_select'] == False:
									body.hide_select = True

								#if bounds hidden/locked
								if bounds_viewport_state['hide_viewport'] == False:
									bounds.hide_viewport = True
								if bounds_viewport_state['hide_get'] == False:
									bounds.hide_set(True)
								if bounds_viewport_state['hide_select'] == False:
									bounds.hide_select = True

							else:
								self.report({'WARNING'}, 'Body and its Boundboxes must be in the collection!')
						else:
							self.report({'WARNING'}, 'Body/Boundboxes are not found in the collection or extra objects are in the collection!')
					else:
						self.report({'WARNING'}, 'Only meshes can be in a Body collection!')
				else:
					self.report({'WARNING'}, 'Collection is empty!')
			else:
				self.report({'WARNING'}, 'Select a special collection that contains a Body mesh and its Boundboxes. Scene Collection is not visible to the Body exporter')
		else:
			self.report({'WARNING'}, 'Selected  directory for export is not valid! Try selecting it again with Relative Path unchecked in the Blender file dialog settings. Do not include a file name in the path.')

		return {'FINISHED'}

class BodiesBatchExport(Operator):
	bl_idname = "object.bodies_batch_export"
	bl_label = "Bodies Batch Export"
	bl_description = "Export Car Bodies in batch mode. Requires a special parent collection containing at least one body collection and exports all not excluded from View Layer"
	bl_options = {'REGISTER', 'UNDO'}

	@classmethod
	def poll(cls, context):
		return context.collection is not None

	def execute(self, context):
		batch_export(self, context, 'Body')
		return {'FINISHED'}

class RimExport(Operator):
	bl_idname = "object.rim_export"
	bl_label = "Rim Export"
	bl_description = "Non-Destructive Rim Export. Select rim(s) collection and press Export Single"
	bl_options = {'REGISTER', 'UNDO'}

	@classmethod
	def poll(cls, context):
		return context.collection is not None

	# export function
	def rim_export(self, collection_name, file_path, apply_transform):
		bpy.ops.export_scene.fbx(
		filepath=(file_path + "/" + collection_name + ".fbx"),
		use_active_collection=True,
		check_existing=False,
		use_selection=True,
		object_types={'MESH'},
		bake_anim=True,
		global_scale=1.0,
		axis_forward='Y',
		axis_up='Z',
		primary_bone_axis='Y',
		secondary_bone_axis='X',
		add_leaf_bones=False,
		apply_unit_scale=True,
		mesh_smooth_type='EDGE',
		use_tspace=False,
		use_mesh_modifiers=False,
		bake_space_transform=apply_transform
		)

	def complex_rim(self, rim_copies):
		rim_copies_count = len(rim_copies)
		if rim_copies_count > 1:
			for copy in rim_copies:
				copy.select_set(True)
			bpy.context.view_layer.objects.active = rim_copies[0]
			bpy.ops.object.join()
			complex_rim = bpy.context.active_object
			bpy.ops.object.select_all(action='DESELECT')
			if complex_rim is not None:
				return complex_rim
			else:
				return None

	def execute(self, context):
		file_path = bpy.context.scene.export_path
		forced_object_mode(self, context, context.object)
		ops = bpy.ops.object
		data = bpy.data.objects
		if_apply_transform	= bpy.context.scene.if_apply_transform

		# if directory exists
		if  os.path.exists(file_path):
			collection = bpy.context.collection
			collection_name = collection.name
			full_name = file_path + validate_export_name(self, collection_name) + '.fbx'
			if bpy.context.selected_objects:
				bpy.ops.object.select_all(action='DESELECT')
			if collection.name != 'Master Collection':
				#get collection's mesh content
				content = [i for i in collection.all_objects[:] if i.type == 'MESH']
				rim_copies = []

				if content:
					bpy.ops.object.select_all(action='DESELECT')

					# start applying modifiers
					for rim in content:
					# make sure Base is active shape key
						if rim.data.shape_keys:
							rim.active_shape_key_index = 0
							keys = rim.data.shape_keys.key_blocks[:]
							for i in keys:
								if i.name != 'Basis':
									if i.value != 0:
										i.value = 0
						# copy
						rim_copies.append(duplicate(self, context, rim))

					for rim_copy in rim_copies:
						bpy.ops.object.select_all(action='DESELECT')
						rim_copy.select_set(True)
						bpy.context.view_layer.objects.active = rim_copy

						#apply modifiers Mirror first
						if rim_copy.name in data:
							indices = get_faces_indices(self, rim_copy)
							if rim_copy.modifiers:
								# if mirror
								if 'Mirror' in rim_copy.modifiers:
									rim_copy.modifiers.active = rim_copy.modifiers['Mirror']
									if_shape_keys(self, rim_copy, 'Mirror', indices)

								# if no mirror
								elif 'Mirror' not in rim_copy.modifiers and 'Triangulate' in rim_copy.modifiers:
									rim_copy.modifiers.active = rim_copy.modifiers['Triangulate']
									if_shape_keys(self, rim_copy, 'Triangulate', indices)

								# apply the rest
								if rim_copy.modifiers:
									i = 0
									# if shape keys
									if rim_copy.data.shape_keys:
										for m in rim_copy.modifiers:
											if m.type != 'ARMATURE':
												rim_copy.modifiers.active = rim_copy.modifiers[i]
												bpy.ops.object.apply_modifiers_with_shape_keys()
												i += 1
									else:
										for m in rim_copy.modifiers:
											ops.modifier_apply(modifier = m.name)
							# UV Unwrap
							if len(rim_copy.data.uv_layers.keys()) < 1:
								bpy.ops.mesh.uv_texture_add()
								bpy.ops.object.mode_set(mode = 'EDIT')
								bpy.ops.mesh.select_all(action='SELECT')
								bpy.ops.uv.unwrap(method='ANGLE_BASED', margin=0)
								bpy.ops.mesh.scale_uvs(command = "SET")
								bpy.ops.mesh.select_all(action='DESELECT')
								bpy.ops.object.mode_set(mode = 'OBJECT')

				# join copies if complex rim
				complex_rim = self.complex_rim(rim_copies)

				#export
				if bpy.context.scene.debug_mode == False:
					if file_path:
						if os.access(full_name, os.W_OK) or os.access(full_name, os.F_OK):
							os.chmod(full_name, 0o744)
						if complex_rim is not None:
							complex_rim.select_set(True)
							bpy.context.view_layer.objects.active = complex_rim

						if bpy.context.scene.export_flag:
							self.rim_export(collection_name, file_path, if_apply_transform)
							self.report({'INFO'}, full_name)
						else:
							self.report({'WARNING'},  "Export Failed! Unequal vertex count of shape keys. Find the debugging details in the console window")
							bpy.context.scene.export_flag = True
						bpy.ops.object.select_all(action='DESELECT')

					else:
						self.report({'WARNING'}, 'File path is not valid!')

				#cleanup
				new_content = [i for i in collection.all_objects[:] if i.type == 'MESH']
				for copy_to_delete in new_content:
					if copy_to_delete not in content:
						if bpy.context.scene.debug_mode == False:
							bpy.data.objects.remove(copy_to_delete, do_unlink=True)
						else:
							copy_to_delete.name = copy_to_delete.name + "_debug"
			else:
				self.report({'WARNING'}, 'Select a Rim Collection to export')
		else:
			self.report({'WARNING'}, 'The directory is not valid! Try selecting it again with Relative Path unchecked in the Blender File Dialog settings')

		return {'FINISHED'}

class RimsBatchExport(Operator):
	bl_idname = "object.rim_batch_export"
	bl_label = "Rim Batch Export"
	bl_description = "Non-Destructive Rim Batch Export. Select a parent Rim Collection and press Export Batch."
	bl_options = {'REGISTER', 'UNDO'}

	@classmethod
	def poll(cls, context):
		return context.collection is not None

	def execute(self, context):
		batch_export(self, context, 'Rim')
		return {'FINISHED'}

class GetSelectedObjectsNames (Operator):
	bl_idname = "object.get_selected_objects_names"
	bl_label = "Get Selected Object Names"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = 'Add selected objects'

	def execute(self, context):

		if bpy.context.selected_objects:
			obj_list = []
			for i in bpy.context.selected_objects:
				obj_list.append(i.name + " ")

			obj_string = ""
			obj_string = obj_string.join(obj_list)
			bpy.context.scene.hierarchy_list = obj_string.rstrip()
		else:
			self.report({'WARNING'},  "Nothing selected")

		return {'FINISHED'}

class FixturesExport(Operator):
	bl_idname = "object.fixture_export"
	bl_label = "Fixtures Export"
	bl_description = "Non-destructive Fixtures Export. Select a Fixture Collection in the Outliner and run the script. The hierarchy of collections should be as Root>[UvMesh,SkinnedMesh,ConformingMesh]"

	@classmethod
	def poll(cls, context):
		return context.collection is not None

	def complex_fixture(self, fixture_copies):
		fixture_copies_count = len(fixture_copies)
		if fixture_copies_count > 1:
			for copy in fixture_copies:
				copy.select_set(True)
			bpy.context.view_layer.objects.active = fixture_copies[0]
			bpy.ops.object.join()
			complex_fixture = bpy.context.active_object
			bpy.ops.object.select_all(action='DESELECT')
			if complex_fixture is not None:
				return complex_fixture
			else:
				return None

	def fixture_export(self, collection_name, file_path, if_apply_transform):
		bpy.ops.export_scene.fbx(
		filepath=(file_path + "/" + collection_name + ".fbx"),
		use_active_collection=False,
		check_existing=False,
		use_selection=True,
		object_types={'MESH', 'ARMATURE'},
		global_scale=1.0,
		axis_forward='Y',
		axis_up='Z',
		primary_bone_axis='Y',
		secondary_bone_axis='X',
		add_leaf_bones=False,
		apply_unit_scale=True,
		mesh_smooth_type='EDGE',
		use_tspace=False,
		use_mesh_modifiers=False,
		bake_space_transform=if_apply_transform
		)

	def execute(self, context):
		file_path = bpy.context.scene.export_path
		ops = bpy.ops.object
		data = bpy.data.objects

		forced_object_mode(self, context, context.object)

		# if directory exists
		if  os.path.exists(file_path):
			collection = context.collection
			if collection is not None:
				if collection.name != 'Scene Collection':
					children_collections = collection.children
					if children_collections:
						count = len(children_collections)
						for collection in children_collections:
							collection_name = collection.name

							full_name = file_path + validate_export_name(self, collection_name) + '.fbx'
							if bpy.context.selected_objects:
								bpy.ops.object.select_all(action='DESELECT')
							if collection.name != 'Scene Collection':
								#get collection's mesh content
								content = [i for i in collection.all_objects[:] if i.type == 'MESH']
								fixture_copies = []

								if content:
									bpy.ops.object.select_all(action='DESELECT')
									# start applying modifiers
									for fixture in content:
										# copy
										fixture_copies.append(duplicate(self, context, fixture))

								if len(fixture_copies) > 0:
									# check if no None fixtures
									none_check = [i for i in fixture_copies if i is not None]
									if len(fixture_copies) == len(none_check):
										for fixture_copy in fixture_copies:
											bpy.ops.object.select_all(action='DESELECT')
											fixture_copy.select_set(True)
											bpy.context.view_layer.objects.active = fixture_copy

											if fixture_copy.data.shape_keys is None:
												if len(fixture_copy.modifiers) > 0 and fixture_copy.type == 'MESH':
													# fix mirrored triangulation
													if 'Mirror' in fixture_copy.modifiers:
														# get half
														indices = get_faces_indices(self, fixture_copy)
														bpy.ops.object.modifier_apply(modifier = 'Mirror')
														fix_mirrored_half_triangulation(self, fixture_copy, indices)

													do_not_apply = ('ARMATURE')
													# apply other modifiers except for armature
													for m in fixture_copy.modifiers:
														if m.type not in do_not_apply:
															bpy.ops.object.modifier_apply(modifier = m.name)
												else:
													self.report({'WARNING'}, self.bl_label + ": " + "Fixtures can't have shape keys! Nothing exported")

										# join copies if complex fixture
										complex_fixture = self.complex_fixture(fixture_copies)

										armature = None
										if complex_fixture is not None:
											armature = get_armature(self, complex_fixture)
										else:
											armature = get_armature(self, fixture_copy)

										if armature is not None and armature.object is not None:											
											armature.object.select_set(True)					

										# if single mesh fixture
										if complex_fixture is None:
											fixture_copy.select_set(True)
											bpy.context.view_layer.objects.active = fixture_copy

										if file_path:
											if os.access(full_name, os.W_OK) or os.access(full_name, os.F_OK):
												os.chmod(full_name, 0o744)
											if complex_fixture is not None:
												complex_fixture.select_set(True)
												bpy.context.view_layer.objects.active = complex_fixture

											# export
											self.fixture_export(collection_name, file_path, context.scene.if_apply_transform)
											self.report({'INFO'}, full_name)

											bpy.ops.object.select_all(action='DESELECT')									

										else:
											self.report({'WARNING'}, 'File path is not valid!')
									else:
										self.report({'WARNING'}, self.bl_label + ": " + "Fixture not found or locked/hidden.")
								else:
									self.report({'WARNING'}, 'Content of Fixtures Collection not found!')

								#cleanup
								new_content = [i for i in collection.all_objects[:] if i.type == 'MESH']
								for copy_to_delete in new_content:
									if copy_to_delete not in content:
										bpy.data.objects.remove(copy_to_delete, do_unlink=True)
					else:
						self.report({'WARNING'}, 'Select the Root Fixture Collection to export all fixture parts')
				else:
					self.report({'WARNING'}, 'Root Fixture Collection not found or not active!')
		else:
			self.report({'WARNING'}, 'The directory is not valid! Try selecting it again with Relative Path unchecked in the Blender File Dialog settings')
		return {'FINISHED'}

class FixturesBatchExport(Operator):
	bl_idname = "object.fixtures_batch_export"
	bl_label = "Fixtures Batch Export"
	bl_description = "Non-destructive Fixtures Batch Export. Select the Root Collection and press Export Batch. The hierarchy of collections should be as Root(Fixture Variants)>Root(Fixture)>[UvMesh,SkinnedMesh,ConformingMesh]"
	bl_options = {'REGISTER', 'UNDO'}

	@classmethod
	def poll(cls, context):
		return context.collection is not None

	def execute(self, context):
		batch_export(self, context, 'Fixture')
		return {'FINISHED'}

class FixturesExportObjectSelected(Operator):
	bl_idname = "object.selected_fixtures_batch_export"
	bl_label = "Non-destructive Selected Fixtures Batch Export"
	bl_description = "Non-destructive Selected Fixtures Batch Export. Select the mesh(es) in Object mode and run the script"

	@classmethod
	def poll(cls, context):
		return context.object is not None

	def export(self, name, file_path, if_apply_transform):
		bpy.ops.export_scene.fbx(
		filepath=(file_path + "/" + name),
		use_active_collection=False,
		check_existing=False,
		use_selection=True,
		object_types={'MESH', 'ARMATURE'},
		global_scale=1.0,
		axis_forward='Y',
		axis_up='Z',
		primary_bone_axis='Y',
		secondary_bone_axis='X',
		add_leaf_bones=False,
		apply_unit_scale=True,
		mesh_smooth_type='EDGE',
		use_tspace=False,
		use_mesh_modifiers=False,
		bake_space_transform=if_apply_transform
		)

	def execute(self, context):
		file_path = bpy.context.scene.export_path
		ao = bpy.context.active_object
		ops = bpy.ops.object
		data = bpy.data.objects
		if_apply_transform	= bpy.context.scene.if_apply_transform

		forced_object_mode(self, context, context.object)

		# if directory exists
		if  os.path.exists(file_path):
			o = bpy.ops.object
			c = bpy.context
			sel = bpy.context.selected_objects

			if sel:
				if c.object.type == "MESH" and c.active_object.mode == 'OBJECT':
					sel = bpy.context.selected_objects
					o.select_all(action='DESELECT')

					for i in sel:
						i.select_set(True)
						bpy.context.view_layer.objects.active = i

			if bpy.context.selected_objects:
				bpy.ops.object.select_all(action='DESELECT')

				content = [i for i in sel if i.type == 'MESH']
				fixture_copies = []

				if content:
					bpy.ops.object.select_all(action='DESELECT')
					# start applying modifiers
					for fixture in content:
						# copy
						fixture_copies.append(duplicate(self, context, fixture))

				if len(fixture_copies) > 0:
					# check if no None fixtures
					none_check = [i for i in fixture_copies if i is not None]
					if len(fixture_copies) == len(none_check):
						for fixture_copy in fixture_copies:
							bpy.ops.object.select_all(action='DESELECT')
							fixture_copy.select_set(True)
							bpy.context.view_layer.objects.active = fixture_copy

							if fixture_copy.data.shape_keys is None:
								if len(fixture_copy.modifiers) > 0 and fixture_copy.type == 'MESH':
									# fix mirrored triangulation
									if 'Mirror' in fixture_copy.modifiers:
										# get half
										indices = get_faces_indices(self, fixture_copy)
										bpy.ops.object.modifier_apply(modifier = 'Mirror')
										fix_mirrored_half_triangulation(self, fixture_copy, indices)

									do_not_apply = ('ARMATURE')
									# apply other modifiers except for armature
									for m in fixture_copy.modifiers:
										if m.type not in do_not_apply:
											bpy.ops.object.modifier_apply(modifier = m.name)
							else:
								self.report({'WARNING'}, self.bl_label + ": " + "Fixtures can't have shape keys!")

						# export
						bpy.ops.object.select_all(action='DESELECT')
						for fixture_copy in fixture_copies:
							fixture_copy.select_set(True)

							bpy.context.view_layer.objects.active = fixture_copy
							full_name = validate_export_name(self, fixture_copy.name) + '.fbx'

							armature = get_armature(self, fixture_copy)
							if armature is not None and armature.object is not None:
								armature.object.select_set(True)	

							if file_path:
								if os.access(full_name, os.W_OK) or os.access(full_name, os.F_OK):
									os.chmod(full_name, 0o744)

								self.export(full_name, file_path, if_apply_transform)
								self.report({'INFO'}, full_name)
								bpy.ops.object.select_all(action='DESELECT')

							else:
								self.report({'WARNING'}, 'Export path is not valid!')

						for obj in sel:
							obj.select_set(True)
						bpy.context.view_layer.objects.active = ao

					else:
						self.report({'WARNING'}, self.bl_label + ": " + "Fixture not found or locked/hidden.")
				else:
					self.report({'WARNING'}, 'Content of Fixtures Collection not found!')

				#cleanup
				for copy_to_delete in fixture_copies:
					bpy.data.objects.remove(copy_to_delete, do_unlink=True)

			else:
				self.report({'WARNING'}, 'Nothing selected')
		else:
			self.report({'WARNING'}, 'The directory is not valid! Try selecting it again with Relative Path unchecked in the Blender File Dialog settings')
		return {'FINISHED'}

class HierarchyExport(Operator):
	bl_idname = "object.fast_auto_fbx_export"
	bl_label = "Fast Auto Fbx Export"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = 'Export Fixtures/Engine Parts or other assets with hierarchy. Each Parent in the hierarchy must be an Empty'

	@classmethod
	def poll(cls, context):
		return context.object is not None

	def get_main_node(self, obj):
		while obj.parent is not None:
			obj = obj.parent
		return obj

	def execute(self, context):
		hier_path = bpy.context.scene.export_path
		forced_object_mode(self, context, context.object)
		obj_list = [obj for obj in context.selected_objects if obj.type == "EMPTY"]
		# if directory exists
		if os.path.exists(hier_path):
			bpy.ops.object.select_all(action='DESELECT')
			if os.path.exists(hier_path):
				if len(obj_list) > 0:
					for _obj in obj_list:
						obj = self.get_main_node(_obj)
						file = (hier_path + obj.name + ".fbx")
						if os.access(file, os.W_OK) or os.access(file, os.F_OK):
							os.chmod(file, 0o744)
						if obj.name in bpy.data.objects:
							obj.select_set(True)
						else:
							self.report({'WARNING'},  "Object doesn't exist")
						#add lod property if lods
						if bpy.context.scene.if_lods:
							if obj.name in bpy.data.objects:
								if 'fbx_type' not in obj:
									obj['fbx_type'] = "LodGroup"
						else:
							#delete lod property if exists and if lods is false
							if obj.name in bpy.data.objects:
								for obj in obj_list:
									if 'fbx_type' in obj:
										del obj['fbx_type']

					# export
					sel = bpy.context.selected_objects
					if len(sel):
						if bpy.context.selected_objects[0].type	== "EMPTY" and bpy.context.selected_objects[0].parent == None:
							bpy.ops.object.non_destructive_export(if_batch = False, file_path = hier_path)
						else:
							bpy.ops.object.non_destructive_export(if_batch = True, file_path = hier_path)
						# temporary fake report
						for i in sel:
							self.report({'INFO'}, hier_path + validate_export_name(self, i.name) + ".fbx")
				else:
					self.report({'WARNING'}, "Selected parent objects must have EMPTY type!")
			else:
				self.report({'WARNING'}, "Export path not found!")
		else:
			self.report({'WARNING'}, 'The directory is not valid! Try selecting it again with Relative Path unchecked in the Blender file dialog settings')
		return {'FINISHED'}


class NonDestructiveExport(Operator):
	bl_idname = "object.non_destructive_export"
	bl_label = "Non-destructive Export"
	bl_description = "Exports selected objects. Converts curves to meshes and corrects flipped normals. Protects exported source objects from modifying"
	hide_lods: bpy.props.BoolProperty(name='Hide LODs', default=True)

	def unhide_viewport(self, obj):
		if obj.hide_viewport:
			obj.hide_viewport = False		
		if obj.hide_get():
			obj.hide_set(False)		
		if obj.hide_select:
			obj.hide_select = False		

	@classmethod
	def poll(cls, context):
		return context.object is not None

	if_batch: bpy.props.BoolProperty()
	file_path: bpy.props.StringProperty()

	source_mirrored_meshes = []
	source_mirrored_curves = []

	def getParent(self):
		sel = bpy.context.selected_objects

		if sel:
			parents = []
			for x in sel:
				if x.parent:
					x.select_set(False)

			parents = bpy.context.selected_objects

			bpy.ops.object.select_all(action='DESELECT')
			for s in sel:
				s.select_set(True)

			return parents

		return None

	def getAllContent(self, parent):
		#returns children objects of the parent node

		if parent is None or parent.type != 'EMPTY':			
			return None

		content = []

		for i in parent.children:
			content.append(i)
			if i.children:
				for ch in i.children:
					content.append(ch)
					if ch.children:
						for skt in ch.children:
							content.append(skt)

		return {True:content, False:None}[len(content)>0]

	# main export function
	def exp(self, obj_name, apply_transform):
		bpy.ops.export_scene.fbx(
		filepath=(self.file_path + "/" + obj_name + ".fbx"),
		check_existing=False,
		use_selection=True,
		object_types={'EMPTY','ARMATURE','MESH'},
		bake_anim=False,
		axis_forward='Y',
		axis_up='Z',
		add_leaf_bones=False,
		use_custom_props=True,
		mesh_smooth_type='EDGE',
		bake_space_transform=apply_transform
		)

	def findCurves(self):
		curves = []
		sel = bpy.context.selected_objects
		parent = bpy.context.object.parent
		if bpy.context.object:
			if parent is not None:
				parent.select_set(True)
				self.getAllContent(parent)
				for i in bpy.context.selected_objects:
					if i.type == 'CURVE' and i.data.bevel_depth > 0:
						curves.append(i)
				if curves:
					return curves
			else:
				for i in sel:
					if i.type == 'CURVE' and i.data.bevel_depth > 0:
						curves.append(i)
						# hide from render for heatmap headers ao bake
						i.hide_render = True

				if curves:
					return curves

			#back selection
			bpy.ops.object.select_all(action='DESELECT')
			for s in sel:
				s.select_set(True)

		return bpy.context.selected_objects

	def convertCurves(self):
		type_check = []
		for obj in bpy.context.selected_objects:
			if obj.type == 'CURVE':
				type_check.append(obj)

		if len(type_check) == 0:
			return []

		convCurves = None
		context = bpy.context		
		sel = context.selected_objects

		self.source_mirrored_curves = self.findCurves()
		if not len(self.source_mirrored_curves) > 0:
			return None

		bpy.ops.object.select_all(action='DESELECT')
		for i in self.source_mirrored_curves:
			i.select_set(True)
		
		for obj in context.selected_objects:
			if obj.type != 'CURVE':
				obj.select_set(False)
		
		bpy.ops.object.duplicate()

		convCurves = context.selected_objects
		for obj in convCurves:
			if obj.type == 'CURVE':
				context.view_layer.objects.active = obj
				obj.select_set(True)
				break

		if not bpy.ops.object.convert.poll():
			bpy.ops.object.select_all(action='DESELECT')			
			for obj in sel:
				obj.select_set(True)
			
			return None

		bpy.ops.object.convert(target='MESH')		
		bpy.ops.object.make_single_user(object=True, obdata=True)				

		for obj in convCurves:			
			obj.select_set(True)
			# unhide rendering for heatmap headers ao bake
			if obj.parent and 'LOD0' in obj.parent.name:
				obj.hide_render = False
			bpy.context.view_layer.objects.active = obj		
			bpy.ops.object.mode_set(mode = 'EDIT')
			bpy.ops.mesh.select_all(action='SELECT')
			bpy.ops.mesh.remove_doubles(threshold=0.001)
			bpy.ops.mesh.unwrap_pipe()
			bpy.ops.mesh.select_all(action='DESELECT')	
			obj.select_set(False)

		#scale uvs
		for obj in convCurves:
			obj.select_set(True)
			bpy.ops.object.mode_set(mode = 'EDIT')
			if context.scene.tool_settings.use_uv_select_sync:
				context.scene.tool_settings.use_uv_select_sync = False
			bpy.ops.uv.select_all(action='SELECT')
			bpy.ops.mesh.scale_uvs(command = "SET")			

		for obj in convCurves:
			# headers only
			mesh = obj.data
			bpy.context.view_layer.objects.active = obj

			if not 'Color' in mesh.attributes:
				bpy.ops.geometry.color_attribute_add(name='Color', domain='POINT', data_type='BYTE_COLOR')
				bpy.ops.geometry.color_attribute_render_set(name='Color')				

		for obj in context.selected_objects:
			if not (obj.parent and 'LOD0' in obj.parent.name):
				obj.select_set(False)

			for collection in obj.users_collection:
				if collection.hide_render:
					collection.hide_render = False

		bpy.ops.object.mode_set(mode = 'OBJECT')
		
		if len(context.selected_objects) > 0:
			if bpy.ops.object.bake.poll() and bpy.context.scene.render.engine == 'CYCLES':
				bpy.ops.object.bake(type='AO')

		for obj in convCurves:
			# headers heatmap	
			if obj.parent and 'HEADERS' in obj.parent.name and 'LOD0' in obj.parent.name:
				bpy.context.view_layer.objects.active = obj
				bpy.ops.object.ao_to_exhaust_heatmap(value=0.5, use_heat_source=True)
			# else:
			# 	mesh = obj.data
			# 	bm = bmesh.new()
			# 	bm.from_mesh(mesh)
			# 	bm.verts.ensure_lookup_table()
			# 	bm.faces.ensure_lookup_table()

			# 	for index, vert in enumerate(bm.verts):								
			# 		color_attribute = mesh.color_attributes['Color'].data.items()[index][1]			
			# 		color_attribute.color = (1.0, 1.0, 1.0, 1.0)

			# 	bm.free()	
				
		bpy.ops.object.mode_set(mode = 'OBJECT')

		# back to the original selection
		bpy.ops.object.select_all(action='DESELECT')
		for obj in sel:
			obj.select_set(True)
		
		return convCurves

	def duplicateMeshesWithNegativeScale(self):
		sel = bpy.context.selected_objects
		self.source_mirrored_meshes.clear()
		
		bpy.ops.object.select_all(action='DESELECT')
		#get flipped
		for m in sel:
			if m.type == 'MESH' and ( m.scale[0] < 0 or m.scale[1] < 0  or m.scale[2] < 0):
				# print(m.scale[0], m.scale[1], m.scale[2])		
				self.source_mirrored_meshes.append(m)
				m.select_set(True)

		if len(self.source_mirrored_meshes) > 0:
			#duplicate
			bpy.ops.object.duplicate()

			#get duplicated meshes
			for f in self.source_mirrored_meshes:
				f.select_set(False)
			duplicatedMeshes = bpy.context.selected_objects
			bpy.ops.object.make_single_user(object=True, obdata=True)
			bpy.ops.object.select_all(action='DESELECT')

			#new selection
			for o in sel:
				o.select_set(True)
			for u in duplicatedMeshes:
				u.select_set(True)
			for f in self.source_mirrored_meshes:
				f.select_set(False)

				f.hide_select=True

			#back selection
			bpy.ops.object.select_all(action='DESELECT')
			for obj in sel:
				obj.select_set(True)

			return duplicatedMeshes

		else:
			for obj in sel:
				obj.select_set(True)
			return None

	def invertFlippedNormals(self, inverted):
		sel = bpy.context.selected_objects

		if inverted:
			bpy.ops.object.select_all(action='DESELECT')

			for t in inverted:
				t.select_set(True)
				neg_axis_list = []
				#find out how many axis are flipped
				for n in t.scale:
					if n < 0:
						neg_axis_list.append(n)

				# print ( + ': ')
				# print ((t.name) + ' : ' + str(len(neg_axis_list)) + ' negative scale axes')
				# print("")

				if neg_axis_list:
					# 0 or 2 inverted axes: apply transform
					# 1 or 3 inverted axis: apply transform and flip_normals

					if len(neg_axis_list) == 1 or len(neg_axis_list) == 3:
						if t.type == 'MESH':
							bpy.context.view_layer.objects.active = t
							bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
							bpy.ops.object.mode_set(mode = 'EDIT')
							bpy.ops.mesh.select_all(action='SELECT')
							bpy.ops.mesh.flip_normals()
							bpy.ops.object.mode_set(mode = 'OBJECT')

					elif len(neg_axis_list) == 0 or len(neg_axis_list) == 2:
						bpy.context.view_layer.objects.active = t
						if t.type == 'MESH':
							bpy.ops.object.mode_set(mode = 'OBJECT')
							bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
				t.select_set(False)

			#back selection
			bpy.ops.object.select_all(action='DESELECT')
			for s in sel:
				s.select_set(True)

	def execute(self, context):
		ao = bpy.context.active_object
		d = bpy.data
		context = bpy.context
		sel = bpy.context.selected_objects
		sel_return = bpy.context.selected_objects
		if_apply_transform	= bpy.context.scene.if_apply_transform
		forced_object_mode(self, context, context.object)

		######################################
		## EXPORT WITH HIERARCHY
		for i in sel:
			if i.type == 'MESH':
				bpy.context.view_layer.objects.active = i

		if context.object:
			if  self.if_batch == False:
				if sel and context.object:
					parents = self.getParent()					
					if len(parents) > 0:
						hidden = []

						#if should be in the scene origin
						obj_positions = []
						obj_rotations = []
						if bpy.context.scene.zeroout_location_and_rotation:
							for p in parents:
								obj_positions.append(p.location.copy())
								obj_rotations.append(p.rotation_euler.copy())
								p.location = (0.0, 0.0, 0.0)
								p.rotation_euler = (0.0, 0.0, 0.0)

						for p in parents:
							bpy.ops.object.select_all(action='DESELECT')
							p.select_set(True)
							bpy.context.view_layer.objects.active = p

							if context.scene.join_root_elements:
								p_copy = node_to_mesh(self, context, p)
								p_name = copy.copy(p.name)

								file = self.file_path + p.name + ".fbx"
								# check file's writing permissions
								if os.access(file, os.W_OK) or os.access(file, os.F_OK):
									os.chmod(file, 0o744)

								bpy.ops.object.object_fix_name()
								self.exp(validate_export_name(self, p.name), if_apply_transform)

								for mesh in p_copy.children:
									bpy.data.objects.remove(mesh, do_unlink=True)
								bpy.data.objects.remove(p_copy, do_unlink=True)

								p.select_set(True)
								bpy.context.view_layer.objects.active = p
								modeling.select_parents_recursive(self, p)

								bpy.ops.object.object_fix_name()

								return {'FINISHED'}

							else:
								for obj in p.children_recursive:
									if obj.hide_viewport == True:
										hidden.append(obj)
										obj.hide_viewport = False
									self.unhide_viewport(obj)															

								content = self.getAllContent(p)

								if content is None:
									continue

								for obj in content:
									if obj.name in context.view_layer.objects:
										obj.select_set(True)

								# find and fix broken materials
								modeling.fix_mat_names(self, content)				

								file = self.file_path + validate_export_name(self, p.name) + ".fbx"
								# check file's writing permissions
								if os.access(file, os.W_OK) or os.access(file, os.F_OK):
									os.chmod(file, 0o744)
								
								# if flipped meshes
								dupl_meshes = self.duplicateMeshesWithNegativeScale()
								if dupl_meshes:															
									self.invertFlippedNormals(dupl_meshes)
									for i in dupl_meshes:
										i.select_set(True)

								# if converted curves
								conv = self.convertCurves()						
								if len(conv) > 0:								
									self.invertFlippedNormals(conv)
									for i in conv:
										i.select_set(True)
								
								# if 'offset_x' in i:
								# 	bpy.ops.transform.translate(value=(i['offset_x'], 0, 0))

								# Export-----------------
								self.exp(validate_export_name(self, p.name), if_apply_transform)

								# Rollbacks -------------
								
								# if 'offset_x' in i:
								# 	bpy.ops.transform.translate(value=(-(i['offset_x']), 0, 0))								

								# Unhide
								if hidden:
									for o in hidden:
										o.hide_viewport = True

								# Unlock
								bpy.ops.object.select_all(action='DESELECT')
								for index, ch in enumerate(p.children):
									ch.hide_select=False									
									ch.select_set(True)	
									if index > 0 and self.hide_lods:
										ch.hide_set(True)					
									if ch.children:
										for ch2 in ch.children:
											ch2.hide_select=False
											if index > 0 and self.hide_lods:
												ch2.hide_set(True)																				
											if ch2.children:
												for ch3 in ch2.children:
													ch3.hide_select=False
													ch3.select_set(True)													
													if index > 0 and self.hide_lods:
														ch3.hide_set(True)
								# Cleanup
								if conv is not None:
									bpy.ops.object.select_all(action='DESELECT')
									for obj in conv:
										bpy.data.objects.remove(obj)										

								if dupl_meshes is not None:
									bpy.ops.object.select_all(action='DESELECT')
									for m in dupl_meshes:
										bpy.data.objects.remove(m)

								#back to original selection
								# bpy.ops.object.select_all(action='DESELECT')
								# print(sel_return)
								# for i in sel_return:
								# 		i.select_set(True)
								# bpy.context.view_layer.objects.active = ao

						if len(obj_positions) and len(obj_rotations):
							for i in range(len(obj_positions)):
								parents[i].location = obj_positions[i]
								parents[i].rotation_euler = obj_rotations[i]

					else:
						self.report({'WARNING'}, "No parent nodes selected")
				else:
					self.report({'WARNING'}, "Nothing selected")


			######################
			##  BATCH EXPORT
			else:
				if bpy.context.selected_objects:

					#if flipped meshes
					dupl_meshes = self.duplicateMeshesWithNegativeScale()
					if dupl_meshes:
						self.invertFlippedNormals(dupl_meshes)
						for i in dupl_meshes:
							i.select_set(True)

					#if converted curves
					conv = self.convertCurves()
					if conv:						
						self.invertFlippedNormals(conv)
						for i in conv:
							i.select_set(True)

					if context.object.type == "MESH" and context.active_object.mode == 'OBJECT':
						sel = context.selected_objects
						bpy.ops.object.select_all(action='DESELECT')
						self.report({'INFO'},  "Batch Export:")
						# final export
						for i in sel:
							# if skinned mesh has armature
							x = i
							x.select_set(state = True, view_layer = context.view_layer)
							context.view_layer.objects.active = x

							if (0 < len([q for q in bpy.context.object.modifiers if q.type == "ARMATURE"])):
								print("Export Skinned Mesh...")
								obj_armature = d.objects[i.name].modifiers["Armature"].object
								d.objects[obj_armature.name].select_set(True)
								d.objects[i.name].select_set(True)

							else:
								print("Export Mesh...")
								if d.objects[i.name].type == "MESH":
									d.objects[i.name].select_set(True)
									#if the mesh has children
									if d.objects[i.name].children:
										bpy.ops.object.select_grouped(type='CHILDREN')
										ch = bpy.context.selected_objects
										for n in ch:
											if bpy.context.object.type == 'EMPTY':
												n.select_set(True)
										d.objects[i.name].select_set(True)
										bpy.context.view_layer.objects.active = d.objects[i.name]

							file = self.file_path + validate_export_name(self, i.name) + ".fbx"

							# check file writing permissions
							if os.access(file, os.W_OK) or os.access(file, os.F_OK):
								os.chmod(file, 0o744)
							self.exp(validate_export_name(self, i.name), if_apply_transform)
							#self.report({'INFO'}, self.file_path + i.name + ".fbx")

							bpy.ops.object.select_all(action='DESELECT')

					# Unlock
					if self.source_mirrored_meshes:
						for i in self.source_mirrored_meshes:
							i.hide_select=False

					if self.source_mirrored_curves:
						for i in self.source_mirrored_curves:
							i.hide_select=False

					# Cleanup
					if conv is not None:
						bpy.ops.object.select_all(action='DESELECT')
						for obj in conv:
							obj.select_set(True)
							bpy.ops.object.delete()

					if dupl_meshes is not None:
						bpy.ops.object.select_all(action='DESELECT')
						for m in dupl_meshes:
							m.select_set(True)
							bpy.ops.object.delete()

					# Back to original selection
					for i in sel_return:
							i.select_set(True)
					bpy.context.view_layer.objects.active = ao

				else:
					self.report({'WARNING'}, "Nothing selected")
		else:
			self.report({'WARNING'}, "Nothing exported")
			for i in sel:
				i.select_set(True)

		return {'FINISHED'}

class CollectionHierarchyExport(Operator):
	bl_idname = 'object.collection_hierarchy_export'
	bl_label = 'Collection Hierarchy Export'
	bl_description = 'Collection Hierarchy Export'
	
	@classmethod
	def poll(cls, context):
		return context.object is not None

	def execute(self, context):
		bpy.ops.object.select_all(action='DESELECT')

		base_collections = context.collection.children_recursive

		for collection in base_collections:
			for lod in collection.objects:
					if lod.type == 'EMPTY' and lod.parent == None:
						lod.select_set(True)
					
		bpy.ops.object.fast_auto_fbx_export()

		return {'FINISHED'}

def collection_hierarchy_export_menu(self, context):
	layout = self.layout
	layout.separator()
	layout.operator(CollectionHierarchyExport.bl_idname, text = 'Export')


class AT_ModularExport(Operator):
	bl_idname = 'object.at_export_modular_mesh'
	bl_label = 'Modular Export'
	bl_description = 'Export an engine part modular mesh. The script unpacks the source mesh by splitting its copy into temporary FRONT, MID and REAR segments, then performs their export and removes them from the scene'
	mode: bpy.props.EnumProperty(items=[
		('SET_LIMITS', 'SetLimits', '', 0),
		('DEBUG', 'Debug', '', 1),
		('EXPORT', 'Export', '', 2)],
		name='Mode', options={'HIDDEN', 'SKIP_SAVE'})	

	bl_options = {'REGISTER', 'UNDO'}

	def at_hierarchy_export_routine(self, segments):
		objects = bpy.data.objects
		segments = [objects[segment] for segment in segments]
		bpy.context.view_layer.objects.active = segments[0]

		for obj in segments:
			obj.select_set(True)
		
		bpy.ops.object.fast_auto_fbx_export()

	def at_create_lods_modular_hierarchy(self, name, lods_count):
		empties = []
		def add_empty(lod_name):
			empty = bpy.data.objects.new(name + lod_name, None)
			empties.append(empty)
			empty.empty_display_size = 0
			bpy.context.layer_collection.collection.objects.link(empty)
			return empty

		for segment in ('_FRONT', '_MID', '_REAR'):
			parent_lod = add_empty(segment)
			
			for index in range(lods_count):
				lod = add_empty(segment + '_LOD' + str(index))
				lod.parent = parent_lod

		return empties

	def at_unpack_mesh_into_segments(self, source, limits, lod_index, depsgraph):
		# <BASE_NAME>_FRONT_MESH_LOD<INDEX>
		# <BASE_NAME>_MID_MESH_LOD<INDEX>
		# <BASE_NAME>_REAR_MESH_LOD<INDEX>

		def unpack(source, segment):
			# make a depsgraph copy of the source
			object_eval = source.evaluated_get(depsgraph)
			mesh = bpy.data.meshes.new_from_object(object_eval, preserve_all_data_layers=True, depsgraph=depsgraph)
			copy = bpy.data.objects.new((source.name[:-4] + segment + '_MESH' + '_LOD' + str(lod_index)), mesh)
			bpy.context.layer_collection.collection.objects.link(copy)
			meshes.append(copy)

			# parent the copy to the source collection
			bpy.data.collections['LOD'+str(lod_index)].objects.link(copy)
			for user_collection in copy.users_collection:
				if user_collection.name not in copy.name:
					user_collection.objects.unlink(copy)
			
			bm = bmesh.new()
			bm.from_mesh(mesh)
			bm.verts.ensure_lookup_table()

			# find verts inside and outside clipping planes
			verts = []

			limits_type = bpy.context.scene.at_modular_limits_type
			color = source.data.color_attributes.active_color

			if limits_type == 'X-Coords':
				match(segment):
					case 'FRONT':
						verts = [vert for vert in bm.verts if round(vert.co.x, 3) <= limits[0]]
					case 'MID':
						verts = [vert for vert in bm.verts if limits[0] <= round(vert.co.x, 3) <= limits[1]]
					case 'REAR':
						verts = [vert for vert in bm.verts if round(vert.co.x, 3) >= limits[1]]

			elif limits_type == 'Color':				
				color_limits = bm.loops.layers.color.get(color.name)

				if color_limits is not None:
					match(segment):
						case 'FRONT':
							verts = [vert for vert in bm.verts for loop in vert.link_loops if loop[color_limits].x == 1]
						case 'MID':
							verts = [vert for vert in bm.verts for loop in vert.link_loops if loop[color_limits].y == 1]
						case 'REAR':
							verts = [vert for vert in bm.verts for loop in vert.link_loops if loop[color_limits].z == 1]
					verts = list(set(verts))
				else:
					self.report({'WARNING'}, source.name + ': ' + 'BMesh can\'t find the Active Color Attribute. If it exists, try converting it to CORNER & BYTE_COLOR')
					return None	
			
			if not len(verts) > 0:
				bm.free()
				return None
			
			# do slicing
			for vert in bm.verts[:]:
				if vert not in verts:
					bm.verts.remove(vert)

			bm.to_mesh(mesh)
			bm.free()

			if color is not None and color.name in copy.data.attributes:
				mesh.attributes.remove(mesh.attributes[color.name])		

			# if the source has 'Wighted Normal' modifier, we want to copy it on a new segment
			source_wn_mod = None
			for mod in source.modifiers:
				if mod.type=='WEIGHTED_NORMAL':
					source_wn_mod = mod

			if source_wn_mod is not None:
				new_wn_mod = copy.modifiers.new('Weigted Normal', 'WEIGHTED_NORMAL')
				if new_wn_mod is not None:
					new_wn_mod.invert_vertex_group = source_wn_mod.invert_vertex_group
					new_wn_mod.keep_sharp = source_wn_mod.keep_sharp
					new_wn_mod.mode = source_wn_mod.mode
					new_wn_mod.thresh = source_wn_mod.thresh
					new_wn_mod.use_face_influence = source_wn_mod.use_face_influence
					new_wn_mod.vertex_group = source_wn_mod.vertex_group
					new_wn_mod.weight = source_wn_mod.weight

			return mesh
			
		meshes = []
		for segment in {'FRONT', 'MID', 'REAR'}:
			unpacked_mesh = unpack(source, segment)			
			if unpacked_mesh is None:
				for mesh in meshes:
					if mesh.data.name in bpy.data.meshes:
						bpy.data.meshes.remove(mesh.data, do_unlink=True)			
				return None

		return meshes

	def set_numeric_limits(self):		
		obj = bpy.context.object
		if obj is not None and obj.type=='MESH':
			# mesh selection update
			bpy.ops.object.mode_set(mode = 'OBJECT')			
			bpy.ops.object.mode_set(mode = 'EDIT')

		bm = bmesh.from_edit_mesh(obj.data)
		bm.verts.ensure_lookup_table()
		verts = [vert.co.x for vert in bm.verts if vert.select]

		if not len(verts) > 0:
			self.report({'ERROR'}, "No vertices/edges selected for setting limits!")
			return {'CANCELLED'}

		bm.free()

		bpy.context.scene.at_modular_numeric_limits = ((min(verts), max(verts)))

	def export(self, context, *, debug=False):
		objects = bpy.data.objects		
		base_name = context.scene.at_modular_mesh_name
		depsgraph = context.evaluated_depsgraph_get()
		limits_type = context.scene.at_modular_limits_type
		if base_name == '':
			self.report({'ERROR'}, 'Base name is an empty string!')
			return{'CANCELLED'}	

		lod0_name = base_name + '_LOD0'
		if not lod0_name in bpy.data.objects:
			self.report({'ERROR'}, 'The scene must contain the source mesh ' + lod0_name + ' for unpacking!')
			return{'CANCELLED'}
		
		# lod0 will be the default active object for start
		lod0 = bpy.data.objects[lod0_name]
		lod0.select_set(True)
		bpy.context.view_layer.objects.active = lod0

		if 	bpy.ops.object.mode_set.poll():
			bpy.ops.object.mode_set(mode = 'OBJECT')
			bpy.ops.object.select_all(action='DESELECT')
		else:
			self.report({'ERROR'}, 'Can\'t select ' +  lod0_name +  ' because it is hidden, unselectable or not in the scene!')
			return{'CANCELLED'}

		# set active colelction to default
		context.view_layer.active_layer_collection = context.view_layer.layer_collection

		if not len(base_name) > 0:
			self.report({'ERROR'}, 'Base name is an empty string!')
			return{'CANCELLED'}

		limits = context.scene.at_modular_numeric_limits

		if not base_name in bpy.data.collections:
			self.report({'ERROR'}, 'Collection ' + base_name + ' not found!')
			return{'CANCELLED'}

		lods_collections = bpy.data.collections[base_name].children
		lods_count = len(lods_collections)

		# geometry and hierarchy tests
		for index, lod_collection in enumerate(lods_collections):
			source_lod_name = base_name +'_LOD'+str(index)
			if not source_lod_name in lod_collection.objects:
				self.report({'ERROR'}, lod_collection.name + ' must contain a source mesh for unpacking!')
				return{'CANCELLED'}

			source_lod = bpy.data.objects[source_lod_name]
			if source_lod.type != 'MESH':
				self.report({'ERROR'}, source_lod.name + ' must be a mesh! The type is ' + source_lod.type)
				return{'CANCELLED'}
			
			if (limits[0], limits[1]) == (0,0) and limits_type == 'X-Coords':
				if not 'Limits' in source_lod.data.attributes:
					self.report({'ERROR'}, 'X-Coordinate limits are not set! They cannot be zeroes!')
					return{'CANCELLED'}

			if 	limits_type == 'Color':
				color = source_lod.data.color_attributes.active_color
				if color is None:	
					self.report({'ERROR'}, source_lod.name + ' does not have an Active Color Attribute!')
					return{'CANCELLED'}			
		#

		if not context.scene.if_lods:
			context.scene.if_lods=True
		
		temp = []
		# build empty modular LOD hierarchy
		temp.extend(self.at_create_lods_modular_hierarchy(base_name, lods_count))

		# unpack meshes
		for lod_index in range(lods_count):
			segment_name = base_name + '_LOD'+str(lod_index)
			
			if not segment_name in objects:
				self.report({'WARNING'}, segment_name + ' not found!')
				continue

			source = objects[segment_name]

			# if the source mesh is hidden in viewport, we have to unhide it for making a copy
			vis = [False, False, False]
			if source.hide_get():
				source.hide_set(False)
				vis[0] = True
			if source.hide_viewport:
				source.hide_viewport = False
				vis[1] = True
			if source.hide_select:
				source.hide_select = False
				vis[2] = True

			bpy.ops.object.select_all(action='DESELECT')
			source.select_set(True)
			bpy.context.view_layer.objects.active = source

			# clear custom normals data on source because we don't want it on new segments to make shading seams between segments		  
			bpy.ops.mesh.customdata_custom_splitnormals_clear()
			
			unpacked_segments = self.at_unpack_mesh_into_segments(source, ((round(limits[0],3), round(limits[1],3))), lod_index, depsgraph)

			if unpacked_segments is None:
				for empty in temp:
					if empty.name in bpy.data.objects:
						bpy.data.objects.remove(empty, do_unlink=True)

				self.report({'ERROR'}, limits_type + ' Limits for' + source.name + ' are not found or set correctly!')
				return {'CANCELLED'}

			temp.extend(unpacked_segments)

			# revert source mesh visibility
			source.hide_set(vis[0])
			source.hide_viewport = vis[1]
			source.hide_select = vis[2]

		# parent meshes
		for index, collection in enumerate(lods_collections):
			for obj in collection.objects:
				if obj.name != base_name+'_LOD'+str(lod_index):
					if '_FRONT_' in obj.name:
						obj.parent = objects[base_name+'_FRONT'+'_LOD'+str(index)]
					elif '_MID_' in obj.name:
						obj.parent = objects[base_name+'_MID'+'_LOD'+str(index)]			
					elif '_REAR_' in obj.name:
						obj.parent = objects[base_name+'_REAR'+'_LOD'+str(index)]
				if obj.type == 'EMPTY':
					pos = obj.location
					if (pos.x < limits[0]):
						obj.parent = objects[base_name+'_FRONT'+'_LOD0']
					elif (limits[1] > pos.x > limits[0]):
						obj.parent = objects[base_name+'_MID'+'_LOD0']						
					elif (pos.x > limits[1]):
						obj.parent = objects[base_name+'_REAR'+'_LOD0']
		
		if not debug:
			self.at_hierarchy_export_routine((
				base_name+'_FRONT',
				base_name+'_MID',
				base_name+'_REAR'
				))

			for obj in temp:
				if obj.type == 'MESH':
					bpy.data.meshes.remove(obj.data, do_unlink=True)
				elif obj.type == 'CURVE':
					bpy.data.curves.remove(obj.data, do_unlink=True)
				else:
					bpy.data.objects.remove(obj, do_unlink=True)		

	def execute(self, context):
		match self.mode:
			case 'SET_LIMITS':
				self.set_numeric_limits()				
			case 'DEBUG':
				self.export(context, debug=True)
			case 'EXPORT':
				self.export(context)

		return {'FINISHED'}

# Functions
def duplicate(cls, context, obj):
	obj.select_set(True)
	bpy.context.view_layer.objects.active = obj
	bpy.ops.object.duplicate()
	bpy.ops.object.select_all(action='DESELECT')
	return context.active_object

def duplicate_hierarchy(cls, context, parent):
	modeling.select_recursive(cls, parent)
	bpy.ops.object.duplicate()
	return context.active_object

def node_to_mesh(cls, context, parent):
	p = duplicate_hierarchy(cls, context, parent)
	p_name = copy.copy(p.name)
	bpy.ops.object.select_all(action='DESELECT')
	p_children = []

	for ch in p.children:
		if ch.type != 'EMPTY':
			continue

		p_children.append(ch)
		modeling.select_recursive(cls, ch)

		p.select_set(False)
		ch.select_set(False)

		sel = context.selected_objects
		if len(sel):
			bpy.context.view_layer.objects.active = context.selected_objects[0]
		else:
			self.report({'WARNING'}, "Mesh selection failed!")
			return {'FINISHED'}

		bpy.ops.object.convert(target='MESH')
		bpy.ops.object.join()
		context.active_object.name = ch.name
		bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')

		p.select_set(True)
		bpy.context.view_layer.objects.active = p
		bpy.ops.object.parent_set(type='OBJECT', keep_transform=True)
		bpy.ops.object.select_all(action='DESELECT')

	for node in p_children:
		if node.name in bpy.data.objects:
			bpy.data.objects.remove(node, do_unlink=True)

	p.select_set(True)
	for ch in p.children:
		ch.select_set(True)

	return p

def get_armature(cls, obj):	
	arm = [mod for mod in obj.modifiers if mod.type == "ARMATURE"]
	if len(arm) > 0:
		return arm[0]
	else:
		return None

def get_faces_indices(cls, obj):
	# called by the class only
	bpy.ops.object.mode_set(mode = 'EDIT')
	bm = bmesh.from_edit_mesh(obj.data)
	pos = [f.index for f in bm.faces]
	bpy.ops.object.mode_set(mode = 'OBJECT')
	return pos

def select_mirrored_faces(cls, obj, indices):
	bpy.ops.object.mode_set(mode = 'EDIT')
	bm = bmesh.from_edit_mesh(obj.data)
	bpy.ops.mesh.select_mode(type='FACE')
	mirrored_faces = [f for f in bm.faces]
	for f in mirrored_faces:
		for match in indices:
			if f.index == match:
				f.select = True
	bm.select_flush(True)
	bmesh.update_edit_mesh(obj.data)
	# invert
	bpy.ops.mesh.select_all(action='INVERT')

def fix_mirrored_half_triangulation(cls, obj, indices):
	if 'Triangulate' in obj.modifiers:
		if obj.modifiers['Triangulate'].quad_method != 'FIXED':
			obj.modifiers['Triangulate'].quad_method = 'FIXED'

		bpy.ops.object.mode_set(mode = 'EDIT')
		bpy.ops.mesh.select_all(action='DESELECT')

		select_mirrored_faces(cls, obj, indices)

		bpy.ops.mesh.rotate_edge_triangulation_quads(quad_method="FIXED_ALTERNATE")
		bpy.ops.object.mode_set(mode = 'OBJECT')

def if_shape_keys(cls, mesh, modifier_name, indices):
	if mesh.data.shape_keys:
		bpy.ops.object.apply_modifiers_with_shape_keys()
	else:
		bpy.ops.object.modifier_apply(modifier = modifier_name)
		fix_mirrored_half_triangulation(cls, mesh, indices)

def batch_export(cls, context, export_type):
	collection = context.view_layer.active_layer_collection
	if collection is not None:
		if collection.name != 'Master Collection':
			children_collections = collection.children
			if children_collections:
				count = len(children_collections)
				for i in children_collections:
					if not i.exclude:
						context.view_layer.active_layer_collection = i
						if export_type == 'Body':
							bpy.ops.object.body_export()
						elif export_type == 'Rim':
							bpy.ops.object.rim_export()
							# deselection needed because rim export works in select mode
							bpy.ops.object.select_all(action='DESELECT')
						elif export_type == 'Fixture':
							bpy.ops.object.fixture_export()
							# deselection needed because fixture export works in select mode
							bpy.ops.object.select_all(action='DESELECT')
			else:
				cls.report({'WARNING'}, 'Batch mode failed. In Outliner select a parent collection that contains children body collections and try again!')
		else:
			cls.report({'WARNING'}, 'Parent Collection cannot not be the Scene Collection!')
	else:
		cls.report({'WARNING'}, 'Parent Collection not found!')

def forced_object_mode(cls, context, obj):
	if context.mode != 'OBJECT':
		noedit_types = ['EMPTY','VOLUME','LIGHT','LIGHT_PROBE','CAMERA','SPEAKER']
		if obj.type not in noedit_types:
			bpy.ops.object.mode_set(mode = 'OBJECT')
			
def validate_export_name(cls, name):	
	if ' ' in name:
		name = name.strip()
	if '.' in name:
		name = name.split('.')[0]
	return name

classes = (
	StandardBatchExport,
	FixturesExportObjectSelected,
	BodyExport,
	BodiesBatchExport,
	RimExport,
	RimsBatchExport,
	GetSelectedObjectsNames,
	FixturesExport,
	FixturesBatchExport,
	HierarchyExport,
	NonDestructiveExport,
	CollectionHierarchyExport,
	AT_ModularExport
	)

# Register
def register():
	for cls in classes:
		bpy.utils.register_class(cls)

	bpy.types.OUTLINER_MT_collection.append(collection_hierarchy_export_menu)

	bpy.types.Scene.export_path = bpy.props.StringProperty(
		name="",
		subtype='FILE_PATH',
		description = 'Body Export File Path'
	)

	bpy.types.Scene.export_flag = bpy.props.BoolProperty(
			name="Export Flag",
			default = True
		)

	bpy.types.Scene.if_apply_modifiers = bpy.props.BoolProperty(
		name="Apply Modifiers",
		description = 'Apply Modifiers when the Body is being exported. Mirrored half will be automatically retriangulated',
		default = True
	)

	bpy.types.Scene.if_lods = bpy.props.BoolProperty(
		name="LODs",
		description = 'Export as LODs',
		default = False
	)

	bpy.types.Scene.if_apply_transform = bpy.props.BoolProperty(
		name="Apply Transform",
		description = 'Might fix scale issue of imported Skeletal Meshes in Unreal Editor',
		default = False
	)

	bpy.types.Scene.join_root_elements = bpy.props.BoolProperty(
		name="Each Node To Mesh",
		description = 'Merge content of each node in the main root into a mesh',
		default = False
	)

	bpy.types.Scene.debug_mode = bpy.props.BoolProperty(
		name="Debug",
		description = "Allows to check the mesh with applied modifiers and shape keys that is added to the collection",
		default = False
	)

	bpy.types.Scene.zeroout_location_and_rotation = bpy.props.BoolProperty(
		name="Reset Location and Rotation",
		description = "Reset Location and Rotation to default values",
		default = False
	)

	bpy.types.Scene.if_move_to_origin = bpy.props.BoolProperty(options={'HIDDEN'}, name = 'Move to Origin')

	bpy.types.Scene.at_modular_mesh_name = bpy.props.StringProperty(name='', description='The base name that is used for generating names of exported sections. It can\'t be empty and is the same as the name of the root collection')
	bpy.types.Scene.at_modular_numeric_limits = bpy.props.FloatVectorProperty(name='', size=2, precision=5, description='Mid section X-axis Left and Right bounds')
	bpy.types.Scene.at_modular_limits_type = bpy.props.EnumProperty(items=[
		('X-Coords','COORDS',  '', 0),
		('Color','COLOUR',  '', 1)
		],
		name='Limits type', description='Select the method of setting the limits for source mesh slicing')

# Unregister
def unregister():
	for cls in reversed(classes):
		bpy.utils.unregister_class(cls)

	bpy.types.OUTLINER_MT_collection.remove(collection_hierarchy_export_menu)
	del bpy.types.Scene.export_path
	del bpy.types.Scene.if_apply_modifiers
	del bpy.types.Scene.debug_mode
	del bpy.types.Scene.zeroout_location_and_rotation
	del bpy.types.Scene.join_root_elements
	del bpy.types.Scene.if_apply_transform
	del bpy.types.Scene.if_move_to_origin
	del bpy.types.Scene.at_modular_mesh_name
	del bpy.types.Scene.at_modular_numeric_limits
	del bpy.types.Scene.at_modular_limits_type
