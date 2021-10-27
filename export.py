import bpy
import bmesh
from bpy.utils import register_class, unregister_class
from bpy.types import Operator
from pathlib import Path
import os

class BodyExport(Operator):
	bl_idname = "object.body_export"
	bl_label = "Body Export"
	bl_description = "Export the Car Body with its Boundboxes located inside their own collection named as a future fbx file. Select the body collection in Outliner ant press [Export Single]. Armature should be in the root Scene Collection only"
	bl_options = {'REGISTER', 'UNDO'}

	@classmethod
	def poll(cls, context):
		return context.collection is not None
	
	# export function
	def exp(self, name, file_path):
		bpy.ops.export_scene.fbx(
		filepath=(file_path + "/" + name + ".fbx"),
		use_active_collection=True,
		check_existing=False,
		use_selection=False,
		object_types={'ARMATURE','MESH'},
		bake_anim=False,
		global_scale=1.0,
		axis_forward='-Y',
		axis_up='Z',
		primary_bone_axis='Y',
		secondary_bone_axis='X',
		add_leaf_bones=False,
		apply_unit_scale=True,
		mesh_smooth_type='OFF',
		use_tspace=False,
		use_mesh_modifiers=False
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
		file_path = bpy.context.scene.body_export_path
		ops = bpy.ops.object
		obj = bpy.context.object

		# if directory exists
		if  os.path.exists(file_path):		
			collection = bpy.context.collection
			name = collection.name

			full_name = file_path + name + '.fbx'

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

									#apply modifiers Mirror first
									if body_copy:
										if body_copy.modifiers:
											# if mirror
											if 'Mirror' in body_copy.modifiers:
												body_copy.modifiers.active = body_copy.modifiers['Mirror']												
												if_shape_keys(self, body_copy, 'Mirror', None)
											
											# if no mirror										
											elif 'Mirror' not in body_copy.modifiers and 'Triangulate' in body_copy.modifiers:
												body_copy.modifiers.active = body_copy.modifiers['Triangulate']
												if_shape_keys(self, body_copy, 'Triangulate', None)
													
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
								if "Armature" in bpy.data.objects and "Armature" not in collection.all_objects:
									armature = bpy.data.objects['Armature']
									armature.select_set(True)
									collection.objects.link(armature)
								# check the export flag
								if bpy.context.scene.export_flag:
									if name:
										if file_path:
											if os.access(full_name, os.W_OK) or os.access(full_name, os.F_OK) == False:
												if bpy.context.scene.debug_mode == False:
													self.exp(name, file_path)
													self.report({'INFO'}, full_name)
											else:
												self.report({'WARNING'}, "Body Export: Nothing exported. Check file's writing permissions!")			
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
	def rim_export(self, collection_name, file_path):
		bpy.ops.export_scene.fbx(
		filepath=(file_path + "/" + collection_name + ".fbx"),
		use_active_collection=True,
		check_existing=False,
		use_selection=True,
		object_types={'MESH'},
		bake_anim=True,
		global_scale=1.0,
		axis_forward='-Y',
		axis_up='Z',
		primary_bone_axis='Y',
		secondary_bone_axis='X',
		add_leaf_bones=False,
		apply_unit_scale=True,
		mesh_smooth_type='OFF',
		use_tspace=False,
		use_mesh_modifiers=False
		)

	#uv scale
	def scale_XY(self, v, s, p ):
		return (p[0] + s[0]*(v[0] - p[0]), p[1] + s[1]*(v[1] - p[1]))

	def uv_scale(self, uv_map, scale, pivot ):
		for uv_index in range(len(uv_map.data) ):
			uv_map.data[uv_index].uv = self.scale_XY( uv_map.data[uv_index].uv, scale, pivot)

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
		file_path = bpy.context.scene.rim_export_path
		ops = bpy.ops.object
		data = bpy.data.objects		
		# if directory exists
		if  os.path.exists(file_path):		
			collection = bpy.context.collection
			collection_name = collection.name
			full_name = file_path + collection_name + '.fbx'
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
							indicies = get_faces_indicies(self, rim_copy)
							if rim_copy.modifiers:
								# if mirror
								if 'Mirror' in rim_copy.modifiers:
									rim_copy.modifiers.active = rim_copy.modifiers['Mirror']												
									if_shape_keys(self, rim_copy, 'Mirror', indicies)
											
								# if no mirror										
								elif 'Mirror' not in rim_copy.modifiers and 'Triangulate' in rim_copy.modifiers:
									rim_copy.modifiers.active = rim_copy.modifiers['Triangulate']
									if_shape_keys(self, rim_copy, 'Triangulate', indicies)
						
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
							bpy.ops.mesh.select_all(action='DESELECT')
							bpy.ops.object.mode_set(mode = 'OBJECT')
				
							#scale UVs
							map_name = rim_copy.data.uv_layers.keys()
							uv_map = rim_copy.data.uv_layers[map_name[0]]	
							self.uv_scale(uv_map, (18.9, 18.9), (0.5, 0.5))

				# join copies if complex rim				
				complex_rim = self.complex_rim(rim_copies)

				#export
				if bpy.context.scene.debug_mode == False:
					if file_path:
						if os.access(full_name, os.W_OK) or os.access(full_name, os.F_OK) == False:
							if complex_rim is not None:
								complex_rim.select_set(True)
								bpy.context.view_layer.objects.active = complex_rim

							if bpy.context.scene.export_flag:									
								self.rim_export(collection_name, file_path)
								self.report({'INFO'}, full_name)
							else:
								self.report({'WARNING'},  "Export Failed! Unequal vertex count of shape keys. Find the debugging details in the console window")
								bpy.context.scene.export_flag = True
							bpy.ops.object.select_all(action='DESELECT')
						else:
							self.report({'WARNING'}, "Rim Export: Nothing exported. Check file's writing permissions!")
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
	bl_description = "Non-destructive Fixtures Export. Select a parent Fixtures Collection and press Export Single"
	
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

	def fixture_export(self, collection_name, file_path):
		bpy.ops.export_scene.fbx(
		filepath=(file_path + "/" + collection_name + ".fbx"),
		use_active_collection=True,
		check_existing=False,
		use_selection=True,
		object_types={'MESH', 'ARMATURE'},
		global_scale=1.0,
		axis_forward='-Y',
		axis_up='Z',
		primary_bone_axis='Y',
		secondary_bone_axis='X',
		add_leaf_bones=False,
		apply_unit_scale=True,
		mesh_smooth_type='OFF',
		use_tspace=False,
		use_mesh_modifiers=False
		)

	def execute(self, context):
		file_path = bpy.context.scene.fixtures_path
		ops = bpy.ops.object
		data = bpy.data.objects
		
		# if directory exists
		if  os.path.exists(file_path):
			collection = context.collection
			if collection is not None:
				if collection.name != 'Master Collection':
					children_collections = collection.children
					if children_collections:
						count = len(children_collections)
						for collection in children_collections:
							collection_name = collection.name

							full_name = file_path + collection_name + '.fbx'
							if bpy.context.selected_objects:
								bpy.ops.object.select_all(action='DESELECT')
							if collection.name != 'Master Collection':				
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
														indicies = get_faces_indicies(self, fixture_copy)
														bpy.ops.object.modifier_apply(modifier = 'Mirror')								
														fix_mirrored_half_triangulation(self, fixture_copy, indicies)

													do_not_apply = ('ARMATURE')
													# apply other modifiers except for armature								
													for m in fixture_copy.modifiers:
														if m.type not in do_not_apply:
															bpy.ops.object.modifier_apply(modifier = m.name)
												else:
													self.report({'WARNING'}, self.bl_label + ": " + "Fixtures can't have shape keys! Nothing exported.")

										# join copies if complex fixture
										complex_fixture = self.complex_fixture(fixture_copies)
					
										armature = None
										if complex_fixture is not None:
											armature = get_armature(self, complex_fixture)
										else:
											armature = get_armature(self, fixture_copy)
					
										if armature is not None:
											armature.select_set(True)

										# if single mesh fixture
										if complex_fixture is None:
											fixture_copy.select_set(True)
											bpy.context.view_layer.objects.active = fixture_copy
					
										if file_path:
											if os.access(full_name, os.W_OK) or os.access(full_name, os.F_OK) == False:
												if complex_fixture is not None:
													complex_fixture.select_set(True)								
													bpy.context.view_layer.objects.active = complex_fixture
												# export
												self.fixture_export(collection_name, file_path)
												self.report({'INFO'}, full_name)

												bpy.ops.object.select_all(action='DESELECT')
											else:
												self.report({'WARNING'}, "Fixture Export: Nothing exported. Check file's writing permissions!")
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
						self.report({'WARNING'}, 'Select a Fixture Collection to export')
				else:
					self.report({'WARNING'}, 'Fixtures Parent Collection is not found or selected!')
		else:
			self.report({'WARNING'}, 'The directory is not valid! Try selecting it again with Relative Path unchecked in the Blender File Dialog settings')
		return {'FINISHED'}

class FixturesBatchExport(Operator):
	bl_idname = "object.fixtures_batch_export"
	bl_label = "Fixtures Batch Export"
	bl_description = "Non-destructive Fixtures Batch Export. Select a master Fixtures Collection and press Export Batch."
	bl_options = {'REGISTER', 'UNDO'}

	@classmethod
	def poll(cls, context):
		return context.collection is not None

	def execute(self, context):	
		batch_export(self, context, 'Fixture')
		return {'FINISHED'}

class HierarchyExport(Operator):
	bl_idname = "object.fast_auto_fbx_export"
	bl_label = "Fast Auto Fbx Export"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = 'Export Fixtures/Engine Parts or other assets with hierarchy. Top Parent is always an Empty.'
	
	@classmethod
	def poll(cls, context):
		return context.mode == "OBJECT" and context.object is not None

	def execute(self, context):
		hier_path = bpy.context.scene.hierarchy_path

		# if directory exists
		if os.path.exists(hier_path):
			# object mode
			if bpy.context.mode != 'OBJECT':
				if bpy.context.object:
					bpy.ops.object.mode_set(mode = 'OBJECT')

			bpy.ops.object.select_all(action='DESELECT')
			if os.path.exists(bpy.context.scene.hierarchy_path):
				obj_list = list(bpy.context.scene.hierarchy_list.split(" "))
				if obj_list:
					for i in obj_list:
						if i in bpy.data.objects:
							bpy.data.objects[i].select_set(True)
						else:
							self.report({'WARNING'},  "Object doesn't exist")
						#add lod property if lods
						if bpy.context.scene.if_lods:
							if i in bpy.data.objects:
								if 'fbx_type' not in bpy.data.objects[i]:
									bpy.data.objects[i]['fbx_type'] = "LodGroup"
						else:
							#delete lod property if exists and if lods is false
							if i in bpy.data.objects:
								for i in obj_list:
									if 'fbx_type' in bpy.data.objects[i]:
										del bpy.data.objects[i]['fbx_type']
					# export
					if bpy.context.selected_objects:
						if bpy.context.selected_objects[0].type	== "EMPTY" and bpy.context.selected_objects[0].parent == None:
							bpy.ops.object.non_destructive_export(if_batch = False, file_path = hier_path)
						else:
							bpy.ops.object.non_destructive_export(if_batch = True, file_path = hier_path)
				else:
					self.report({'WARNING'}, "Export list is empty!")
			else:
				self.report({'WARNING'}, "Export path not found!")
		else:
			self.report({'WARNING'}, 'The directory is not valid! Try selecting it again with Relative Path unchecked in the Blender file dialog settings.')
		return {'FINISHED'}

class NonDestructiveExport(Operator):   
	bl_idname = "object.non_destructive_export"
	bl_label = "Non-destructive Export"
	bl_description = "Exports selected objects with hierarchy and without. Converts curves to meshes and corrects flipped normals. Protects exported source objects from modifing."

	@classmethod
	def poll(cls, context):
		return context.mode == "OBJECT" and context.object is not None

	if_batch: bpy.props.BoolProperty()
	file_path: bpy.props.StringProperty()

	source_mirrored_meshes = []
	source_mirrored_curves = []
	
	def getParent(self):
		obj = bpy.ops.object
		sel = bpy.context.selected_objects
		o = bpy.context.object

		if sel:			
			parents = []											
			for x in sel:
				if x.parent:
					x.select_set(False)
					
			parents = bpy.context.selected_objects
			return parents

			#back selection
			obj.select_all(action='DESELECT')
			for s in sel:
				s.select_set(True)

	def getAllContent(self):
		#returns children objects of the parent node
		obj = bpy.ops.object
		c = bpy.context			
		sel = bpy.context.selected_objects

		if c.object:
			parent_list = self.getParent()
			parent = parent_list[0]

			if parent:
				parent.select_set(True)
				if parent.type == "EMPTY":
					for i in parent.children:
						i.select_set(True)
						if i.children:        
							for ch in i.children:
								ch.select_set(True)
								if ch.children:
									for skt in ch.children:
										skt.select_set(True)
			else:
				self.report({'WARNING'}, "No parent nodes selected")			

			content = bpy.context.selected_objects			
			
			#back selection
			obj.select_all(action='DESELECT')
			for s in sel:
				s.select_set(True)

			return content
		
		else:
			self.report({'WARNING'}, "There is no hierarchy")
	
	# main export function
	def exp(self, obj_name):
		bpy.ops.export_scene.fbx(filepath=(self.file_path + "/" + obj_name + ".fbx"), check_existing=False, use_selection=True, object_types={'EMPTY','ARMATURE','MESH'}, bake_anim=False, axis_forward='Y', axis_up='Z', add_leaf_bones=False, use_custom_props=True)
	
	def findCurves(self):
		obj = bpy.ops.object

		curves = []
		sel = bpy.context.selected_objects

		if bpy.context.object:
			if bpy.context.object.parent:				
				bpy.context.object.parent.select_set(True)		
				self.getAllContent()
				for i in bpy.context.selected_objects:
					if i.type == 'CURVE':
						curves.append(i)
				if curves:			
					return curves					
			else:				
				for i in sel:
					if i.type == 'CURVE':
						curves.append(i)
				if curves:			
					return curves

			#back selection
			obj.select_all(action='DESELECT')
			for s in sel:
				s.select_set(True)

	def convertCurves(self):
		obj = bpy.ops.object
		sel = bpy.context.selected_objects
		o = bpy.context.object

		self.source_mirrored_curves = self.findCurves()	
		if self.source_mirrored_curves is not None:
			bpy.ops.object.select_all(action='DESELECT')
			for i in self.source_mirrored_curves:
				i.select_set(True)
			
			bpy.ops.object.duplicate()			
			
			for q in self.source_mirrored_curves:
				q.select_set(False)

			convCurves = bpy.context.selected_objects
			bpy.context.view_layer.objects.active = convCurves[0]
			bpy.ops.object.convert(target='MESH')
			bpy.ops.object.make_single_user(object=True, obdata=True)
			bpy.ops.object.select_all(action='DESELECT')		

			# add duplicates to the original selection
			for o in sel:
				o.select_set(True)
			for u in convCurves:
				u.select_set(True)
			for q in self.source_mirrored_curves:
				q.select_set(False)

				q.hide_select=True			

			#back selection
			obj.select_all(action='DESELECT')
			for s in sel:
				s.select_set(True)					

			return convCurves

	def duplicateMeshesWithNegativeScale(self):
		obj = bpy.ops.object
		sel = bpy.context.selected_objects

		self.source_mirrored_meshes = []
		bpy.ops.object.select_all(action='DESELECT')
		#get flipped
		for m in sel:
			if m.type == 'MESH' and m.scale[0] < 0 or m.scale[1] < 0  or m.scale[2] < 0:				
				self.source_mirrored_meshes.append(m)				 
				m.select_set(True)

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
		obj.select_all(action='DESELECT')
		for s in sel:
			s.select_set(True)
			
		return duplicatedMeshes		

	def invertFlippedNormals(self, inverted):
		obj = bpy.ops.object
		sel = bpy.context.selected_objects

		if inverted:			
			obj.select_all(action='DESELECT')
			
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
			obj.select_all(action='DESELECT')
			for s in sel:
				s.select_set(True)

	def execute(self, context):			   
		obj = bpy.ops.object
		ao = bpy.context.active_object
		d = bpy.data
		c = bpy.context
		sel = bpy.context.selected_objects
		sel_return = bpy.context.selected_objects
		name : bpy.props.StringProperty()				

		######################################
		## EXPORT FILES/LODS WITH HIERARCHY		

		for i in sel:
			if i.type == 'MESH':
				bpy.context.view_layer.objects.active = i		
		
		if c.object:
			if  self.if_batch == False:				
				if sel and c.object:					
					parents = self.getParent()
					if parents:							
						hidden = []
						for p in parents:
							bpy.ops.object.select_all(action='DESELECT')
							p.select_set(True)
							bpy.context.view_layer.objects.active = p						

							if p:
								for o in p.children:
									if o.hide_viewport == True:
										hidden.append(o)
										o.hide_viewport = False	
								
								content = self.getAllContent()								
								for c in content:
									c.select_set(True)						
							
								file = self.file_path + p.name + ".fbx"
								# check file's writing permissions
								if os.access(file, os.W_OK) or os.access(file, os.F_OK) == False:

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

									# Export
									self.exp(p.name)									
									self.report({'INFO'}, file)
																											
									# if hidden 
									if hidden:
										for o in hidden:
											o.hide_viewport = True

									# Unlock
									obj.select_all(action='DESELECT')
									for ch in p.children:										
										ch.hide_select=False
										ch.select_set(True)	
										if ch.children:
											for ch2 in ch.children:
												ch2.hide_select=False
												ch2.select_set(True)
												if ch2.children:
													for ch3 in ch2.children:
														ch3.hide_select=False
														ch3.select_set(True)
									# Cleanup							
									if conv is not None:
										bpy.ops.object.select_all(action='DESELECT')
										for c in conv:
											c.select_set(True)
											bpy.ops.object.delete()

									if dupl_meshes is not None:			
										bpy.ops.object.select_all(action='DESELECT')
										for m in dupl_meshes:
											m.select_set(True)
											bpy.ops.object.delete()

									#back to original selection
									for i in sel_return:
											i.select_set(True)
									bpy.context.view_layer.objects.active = ao
								else:
									self.report({'WARNING'}, "Nothing exported. Check file's writing permissions")
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

					if c.object.type == "MESH" and c.active_object.mode == 'OBJECT':				 
						sel = bpy.context.selected_objects
						obj.select_all(action='DESELECT')   
						self.report({'INFO'},  "Batch Export:")
						# final export
						for i in sel:					   
							# if skinned mesh has armature
							x = i
							x.select_set(state = True, view_layer = bpy.context.view_layer)
							bpy.context.view_layer.objects.active = x
							
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
							
							file = self.file_path + i.name + ".fbx"
							
							# check file writing permissions
							if os.access(file, os.W_OK) or os.access(file, os.F_OK) == False:
								self.exp(i.name)
								self.report({'INFO'}, self.file_path + i.name + ".fbx")
							else:
								self.report({'WARNING'}, "Nothing exported! Check file's writing permissions")
							obj.select_all(action='DESELECT')					

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
						for c in conv:
							c.select_set(True)
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

# Functions
def duplicate(cls, context, obj):
	obj.select_set(True)
	bpy.context.view_layer.objects.active = obj
	bpy.ops.object.duplicate()
	bpy.ops.object.select_all(action='DESELECT')
	return context.active_object
def get_armature(cls, obj):
	if (0 < len([q for q in obj.modifiers if q.type == "ARMATURE"])):
		armature = obj.modifiers["Armature"].object
		return armature
	else:
		return None
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
def if_shape_keys(cls, mesh, modifier_name, indicies):
	if mesh.data.shape_keys:
		bpy.ops.object.apply_modifiers_with_shape_keys()
	else:
		bpy.ops.object.modifier_apply(modifier = modifier_name)
		fix_mirrored_half_triangulation(cls, mesh, indicies)
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

classes = (
	BodyExport,
	BodiesBatchExport,
	RimExport,
	RimsBatchExport,
	GetSelectedObjectsNames,
	FixturesExport,
	FixturesBatchExport,
	HierarchyExport,
	NonDestructiveExport	
	)

# Register
def register():
	for cls in classes:
		bpy.utils.register_class(cls)

	bpy.types.Scene.body_list = bpy.props.StringProperty(
		name='',
		default='',
		description = 'Select one or more objects with hierarchy.'
		)

	bpy.types.Scene.body_export_path = bpy.props.StringProperty(
		name="",
		subtype='FILE_PATH',
		description = 'Body Export File Path'
	)

	bpy.types.Scene.rim_export_path = bpy.props.StringProperty(
		name="",
		subtype='FILE_PATH',
		description = 'Rim Export File Path'
	)
	
	bpy.types.Scene.export_flag = bpy.props.BoolProperty(
			name="Export Flag",
			default = True
		)

	bpy.types.Scene.if_apply_modifiers = bpy.props.BoolProperty(
		name="Apply Modifiers",
		description = 'Apply Modifiers when the Body is being exported. Mirrored half will be automatically retriangulated.',
		default = True
	)

	bpy.types.Scene.hierarchy_list = bpy.props.StringProperty(
		name='',
		default='',
		description = 'Select one or more objects with hierarchy.'
		)

	bpy.types.Scene.hierarchy_path = bpy.props.StringProperty(
		name='', 
		subtype='FILE_PATH',
		description = 'File Path'
		)

	bpy.types.Scene.fixtures_path = bpy.props.StringProperty(
		name="",
		subtype='FILE_PATH',
		description = 'File Path'
	)
	bpy.types.Scene.if_lods = bpy.props.BoolProperty(
		name="LODs",
		description = 'Export as LODs',
		default = False
	)

	bpy.types.Scene.debug_mode = bpy.props.BoolProperty(
		name="Debug",
		description = "Allows to check the mesh with applied modifiers and shape keys that is added to the collection.",
		default = False
	)

# Unregister
def unregister():
	for cls in reversed(classes):
		bpy.utils.unregister_class(cls)

	bpy.types.Scene.body_export_path
	bpy.types.Scene.if_apply_modifiers
	bpy.types.Scene.hierarchy_list
	bpy.types.Scene.hierarchy_path
	bpy.types.Scene.fixtures_path
	bpy.types.Scene.rim_export_path
	bpy.types.Scene.debug_mode
