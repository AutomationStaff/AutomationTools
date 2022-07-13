
import bpy
from bpy.utils import register_class, unregister_class
from bpy.types import Operator

class DrawBrushBlendToggle(Operator):
	bl_label = "Set Weight Paint Brush"
	bl_idname = "brush.draw_brush_blend_toggle"
	bl_description = "Toggle between Draw Brush Add and Sub blend types"
	bl_options = {'REGISTER', 'UNDO'}
	mode : bpy.props.StringProperty(name="Mode", options = {'HIDDEN'})

	@classmethod
	def poll(cls, context):
		return 	_class_method_mesh_and_armature_(cls, context)
	
	def execute(self, context):
		if bpy.context.scene.active_mesh in bpy.data.objects:
			obj = bpy.data.objects[bpy.context.scene.active_mesh]

			if obj.data.use_paint_mask_vertex == False:
					obj.data.use_paint_mask_vertex = True

			if obj and obj.type == 'MESH':
				if bpy.context.mode != 'PAINT_WEIGHT':				
					bpy.ops.object.weight_paint_mode_on()
				#else:
				#	lock_and_select(self, obj)

				bpy.ops.wm.tool_set_by_id(name="builtin_brush.Draw")
				draw_brush = bpy.data.brushes["Draw"]
				bpy.ops.object.weight_paint_mode_on()
				brush = bpy.context.tool_settings.weight_paint.brush
				if brush != 'Draw':
					bpy.context.tool_settings.weight_paint.brush = draw_brush
				
				draw_brush.blend = self.mode
		else:
			self.report({'WARNING'}, 'Skinned Mesh is not found!')

		return {'FINISHED'}

class GenerateRig (Operator):	
	bl_idname = "object.generate_rig"
	bl_label = "Generate Rig"
	bl_description = "Add Car Body Bones"
	bl_options = {'REGISTER', 'UNDO'}	
	name : bpy.props.StringProperty(name="Name")
	symmetry : bpy.props.BoolProperty(name="Symmetry", default=False)
	
	@classmethod
	def poll(cls, context):
		obj = context.object
		sel = len(context.selected_objects)

		if obj is not None and sel > 0:
			if sel == 1:
				if obj.type == 'MESH':
					return True
			elif sel == 2 and sel[0] == 'MESH' or sel[1].type == 'MESH':
				if 'Armature' in sel[0].modifiers or 'Armature' in sel[1].modifiers:
					return True
			elif sel == 2 and obj.type == 'ARMATURE':
				return True
	
	# need to add support of active_mesh to select rig and add bones to it directly
	def execute(self, context):	
		ops = bpy.ops
		obj = bpy.context.object
		data = bpy.data.objects
		scene = bpy.context.scene
		context = bpy.context
		sel = bpy.context.selected_objects
		
		if  len(sel) > 1:
			for o in sel:
				if o.type == 'MESH':
					bpy.context.view_layer.objects.active = o
			obj = bpy.context.object 


		armature = None
		if 'Armature' not in obj.modifiers or obj.modifiers['Armature'].object is None:
			add_armature(self)
			armature = bpy.context.scene.objects[-1]
		
		armature = obj.modifiers['Armature'].object

		armature.select_set(True)
		bpy.context.view_layer.objects.active = armature		
		
		object = armature
		ops.object.mode_set(mode = 'EDIT')
		
		# root
		root = object.data.edit_bones[0]
		if root.name != 'Root':
			root.name = 'Root'

		# add a new bone
		ops.armature.bone_primitive_add(name=self.name)
		new_bone = object.data.edit_bones[-1]
		
		length = scene.bone_length
		
		if  length is not None:
			new_bone.length = length*100
		else:
			new_bone.length = 0.1		


		ops.armature.select_linked()
		ops.armature.select_all(action='DESELECT')

		# parenting
		new_bone.select = True
		root.select = True
		object.data.edit_bones.active = root
		ops.armature.select_linked()		
		ops.armature.parent_set(type='OFFSET')

		# select new bone 
		ops.armature.select_all(action='DESELECT')
		new_bone.select = True		
		
		# add bone constraints
		object.data.edit_bones.active = new_bone
		bpy.ops.object.pose_mode_on()
		bpy.ops.pose.constraint_add(type='LIMIT_LOCATION')
		bpy.context.object.pose.bones[new_bone.name].constraints["Limit Location"].use_transform_limit = True

		ops.object.mode_set(mode = 'EDIT')
		
		ops.armature.select_linked()

		# symmetry
		if self.symmetry is True:
			bpy.ops.transform.translate(value=(-150, 0, 0), orient_type='GLOBAL')
			bpy.ops.armature.symmetrize(direction='NEGATIVE_X')
			object.data.edit_bones[-1].select = True
			new_bone.select = True
		
		#if auto sync
		if bpy.context.scene.auto_add_vertex_group:	
			ops.object.object_edit_mode_on(mode="OBJECT")
			ops.object.select_all(action='DESELECT')			
			obj.select_set(True)			
			context.view_layer.objects.active = obj
			ops.object.sync_vg()		

		#back to the new bone selection
		context.view_layer.objects.active = armature
		armature.select_set(True)
		context.view_layer.objects.active = armature
		ops.object.object_edit_mode_on(mode="EDIT")

		return {'FINISHED'}

class AddArmatureMod (Operator):
	bl_idname = "object.add_armature_mod"
	bl_label = "Add Armature Modifier"
	bl_description = "Add Armature and/or Armature Modifier"
	bl_options = {'REGISTER', 'UNDO'}
	name: bpy.props.StringProperty(options={'HIDDEN'})
	bl_description = "Add Armature and Armature modifier to the selected mesh"

	@classmethod
	def poll(cls, context):
		return bpy.context.object is not None

	def execute(self, context):
		add_armature(self)
		return {'FINISHED'}

class ScaleAllBones (Operator):
	bl_idname = "object.scale_all_bones"
	bl_label = "Apply Bone Scale"
	bl_description = "Apply Bone Scale"
	bl_options = {'REGISTER', 'UNDO'}	
	
	@classmethod
	def poll(cls, context):
		return bpy.context.object is not None and bpy.context.object.type =='ARMATURE'	
	
	def execute(self, context):		
		length = bpy.context.scene.bone_length
		bpy.ops.object.mode_set(mode = 'EDIT')			
		bones = context.object.data.edit_bones
		for bone in bones:
			bone.length = length * 100
		bpy.ops.object.mode_set(mode = 'OBJECT')

		return {'FINISHED'}

class SyncVG (Operator):
	bl_idname = "object.sync_vg"
	bl_label = "Sync Vertex Groups"
	bl_description = "Add Vertex Groups named as Bones"
	bl_options = {'REGISTER', 'UNDO'}

	@classmethod
	def poll(cls, context):
		return _class_method_armature_(cls, context)
	
	def execute(self, context):
		mode = bpy.context.mode	
		obj = bpy.context.object
		bpy.ops.object.select_all(action='DESELECT')
		bpy.ops.object.object_edit_mode_on(mode="OBJECT")
		if obj and obj.hide_get() == False and obj.hide_select == False and obj.hide_viewport == False:
			if obj.type =='MESH':				
				bpy.ops.object.mode_set(mode = 'OBJECT')
					
				bones_list = get_bones(self)

				#add vertex groups
				obj.select_set(True)
				bpy.context.view_layer.objects.active = obj
						
				#sync
				vg = obj.vertex_groups
				vg_names = []
				for v in vg:
					vg_names.append(v.name)				

				k = 0
				for b in bones_list:						
					if b.name not in vg_names:								
						bpy.ops.object.vertex_group_add()
						vg = obj.vertex_groups
						#rename							
						vg[-1].name = b.name
						k += 1
						
						##assign zero weight 
						#weight = bpy.context.scene.tool_settings.vertex_group_weight
						#bpy.context.scene.tool_settings.vertex_group_weight = 0
						#bpy.ops.object.mode_set(mode = 'EDIT')

						#obj.vertex_groups.active = vg[-1]

						#bpy.ops.mesh.select_all(action='SELECT')
						#bpy.ops.object.vertex_group_assign()
						#bpy.context.scene.tool_settings.vertex_group_weight = weight
														
				# lock unused
				if bpy.context.scene.lock_all_unused_vgs:
					lock_unused(self, obj)

				if k > 0:
					self.report({'INFO'}, (str(k) + " Vertex Group(s) added."))
				else:
					self.report({'INFO'}, 'Nothing changed.')

				go_back_to_initial_mode(self, mode)

				set_properties_to_data(self)
		else:
			self.report({'WARNING'}, 'Skinned Mesh is hidden or locked!')

		return {'FINISHED'}

class SelectBonesAndMode(Operator):
	bl_idname = "armature.select_bones_and_mode"
	bl_label = "Select Bone"
	bl_description = "Fast Bone Selection in Edit/Pose/Weight Paint modes."
	bl_options = {'REGISTER', 'UNDO'}
	name: bpy.props.StringProperty(options = {'HIDDEN'})	

	@classmethod
	def poll(cls, context):
		return _class_method_mesh_and_armature_(cls, context)

	def execute(self, context):
		obj = bpy.data.objects[bpy.context.scene.active_mesh]
		bpy.context.view_layer.objects.active = obj

		wp = bpy.context.scene.weight_paint_on_off		
		pose = bpy.context.scene.pose_on_off
		edit = bpy.context.scene.edit_on_off
			
		arm_obj = bpy.data.objects[bpy.context.scene.active_mesh].modifiers['Armature'].object
		armature = arm_obj.data
		bones = get_bones(self)
		bone_count = len(bones)

		bones_names = []
		for b in bones:
			bones_names.append(b.name)
			
		name = self.name
		if name and bones_names:							
			if name in bones_names:
				# make sure armature selected
				bpy.context.view_layer.objects.active = arm_obj
				bpy.ops.object.object_edit_mode_on(mode="EDIT")
				bpy.ops.armature.select_all(action='DESELECT')
				bone = armature.edit_bones[name]
				bone.select = True
				armature.edit_bones.active = bone
				update_selection(self)
			else:
				self.report({'WARNING'}, (name + ' not found!'))

		bpy.ops.armature.select_linked()
		if wp:
			bpy.ops.object.weight_paint_mode_on()			
		elif pose:
			bpy.ops.object.pose_mode_on()				
		if edit:						
			bpy.ops.object.object_edit_mode_on(mode="EDIT")			
					
		set_properties_to_data(self)
									

		return {'FINISHED'}

class SelectVGtoBone(Operator):
	bl_idname = "object.select_vg_to_bone"
	bl_label = "Select active Vertex Group Bone"
	bl_description = "Select Bone connected to the active Vertex Group."
	bl_options = {'REGISTER', 'UNDO'}
	
	@classmethod
	def poll(cls, context):
		return _class_method_mesh_and_armature_(cls, context)

	def execute(self, context):
		update_selection(self)		
		
		if bpy.context.scene.active_mesh in bpy.data.objects:
			obj = bpy.context.scene.active_mesh
			
			if bpy.data.objects[obj].vertex_groups:
				name = bpy.data.objects[obj].vertex_groups.active.name
				
				if "Armature" in context.object.modifiers:					
					wp = bpy.context.scene.weight_paint_on_off		
					pose = bpy.context.scene.pose_on_off
					edit = bpy.context.scene.edit_on_off

					arm_obj = context.object.modifiers['Armature'].object
					armature = arm_obj.data	
					bones = get_bones(self)
					bone_count = len(bones)

					bones_names = []
					for b in bones:
						bones_names.append(b.name)
					
					update_selection(self)
					# bpy.ops.object.object_edit_mode_on(mode='EDIT')
					
					# make sure the armature is selected			
					bpy.context.view_layer.objects.active = arm_obj
					bpy.ops.object.object_edit_mode_on(mode="EDIT")
					
					if name and bones_names:
						update_selection(self)				
						if name in bones_names:
							# make sure armature selected
							bpy.context.view_layer.objects.active = arm_obj
							bpy.ops.armature.select_all(action='DESELECT')

							bone = armature.edit_bones[name]
							bone.select = True
							armature.edit_bones.active = bone
							update_selection(self)					
							bpy.ops.armature.select_linked()			
							if wp:
								bpy.ops.object.weight_paint_mode_on()
							if pose:
								bpy.ops.object.pose_mode_on()
							if edit:
								bpy.ops.object.object_edit_mode_on(mode = 'EDIT')
								bpy.context.view_layer.objects.active = arm_obj

							set_properties_to_data(self)
						else:			
							self.report({'WARNING'}, (name + ' not found!'))
			else:
				self.report({'WARNING'}, (obj + ' Vertex Groups not found!'))
		else:
			self.report({'WARNING'}, ('Skinned Mesh not found!'))	

		return {'FINISHED'}

class StateEditPoseWPButtons (Operator):
	bl_idname = "scene.state_edit_pose_wp_buttons"
	bl_label = "Mode"
	bl_description = "Pin Mode. Requires Active Mesh picked"
	bl_options = {'REGISTER', 'UNDO'}
	wp_on: bpy.props.BoolProperty(options={'HIDDEN'})
	pose_on: bpy.props.BoolProperty(options={'HIDDEN'})
	edit_on: bpy.props.BoolProperty(options={'HIDDEN'})

	@classmethod
	def poll(cls, context):
		return _class_method_mesh_and_armature_(cls, context)

	def execute(self, context):		
		bpy.context.scene.weight_paint_on_off = self.wp_on
		bpy.context.scene.pose_on_off = self.pose_on
		bpy.context.scene.edit_on_off = self.edit_on

		if bpy.context.scene.weight_paint_on_off:
			bpy.ops.object.weight_paint_mode_on()
		if bpy.context.scene.pose_on_off:
			bpy.ops.object.pose_mode_on()
		if bpy.context.scene.edit_on_off:			
			bpy.ops.object.object_edit_mode_on(mode = 'EDIT')			
			bpy.context.view_layer.objects.active = bpy.data.objects[bpy.context.scene.active_mesh].modifiers['Armature'].object

		return {'FINISHED'}

class ShiftVertexWeights(Operator):
	bl_idname = "object.shift_weights"
	bl_label = "Shift Vertex Weights"
	bl_description = "Increase or Decrease Weight of each Vertex in the Active Vertex Group"
	bl_options = {'REGISTER', 'UNDO'}
	action: bpy.props.BoolProperty(options = {'HIDDEN'})

	@classmethod
	def poll(cls, context):
		return _class_method_mesh_(cls, context)	 
	
	def execute(self, context):
		if bpy.context.scene.active_mesh in bpy.data.objects:
			obj = bpy.data.objects[bpy.context.scene.active_mesh]

			mode = bpy.context.mode
			value = bpy.context.scene.vertex_weight_input

			if bpy.context.mode != 'OBJECT':
				bpy.ops.object.mode_set(mode = 'OBJECT')			
			obj = bpy.data.objects[bpy.context.scene.active_mesh]			

			if obj:
				vg = obj.vertex_groups.active														
				if vg:
					if vg.lock_weight == False:
						ind = []
						cont = [vert for vert in obj.data.vertices if vg.index in [i.group for i in vert.groups]]
						
						for i in cont:
							ind.append(i.index)					
						
						if ind:
							if self.action:
								for v in ind:							
									vg.add([v], (vg.weight(v) + value), 'REPLACE')
							else:
								for v in ind:							
									vg.add([v], (vg.weight(v) - value), 'REPLACE')
					else:
						self.report({'WARNING'}, ('Nothing changed.' + '"' + vg.name + '"' + ' is locked.'))

			# original mode
			go_back_to_initial_mode(self, mode)

		else:
			self.report({'WARNING'}, 'Skinned Mesh is not found!')		

		return {'FINISHED'}

class FillActiveVG(Operator):
	bl_idname = "object.fill_active_vg"
	bl_label = "Assign Weight"
	bl_description = "Assign weight to selected vertices"
	bl_options = {'REGISTER', 'UNDO'}
	mode: bpy.props.StringProperty(options={'HIDDEN'})
	multiplier:  bpy.props.IntProperty(options={'HIDDEN'})
	@classmethod
	def poll(cls, context):
		return bpy.context.object is not None	
	
	def execute(self, context):
		if self.mode == 'ADD':
			bpy.context.scene.vert_assign_mode_enum = 'ADD'
		elif self.mode == 'SUBTRACT':
			bpy.context.scene.vert_assign_mode_enum = 'SUBTRACT'
		else:
			bpy.context.scene.vert_assign_mode_enum = 'REPLACE'

		mode = bpy.context.mode

		value = None
		weight = bpy.context.scene.vertex_weight_input
		min_weight = context.scene.tool_settings.vertex_group_weight
		if self.multiplier > 0:
			value = self.multiplier * weight			
		else:
			value = weight

		if bpy.context.mode != 'OBJECT':
			bpy.ops.object.mode_set(mode = 'OBJECT')
			
		sel = context.selected_objects	
		
		if len(sel):
			for obj in sel:				
				bpy.context.view_layer.objects.active = obj				
				vg = obj.vertex_groups.active
				if vg:
					if vg.lock_weight == False:
						ind = []						
						cont = [vert for vert in obj.data.vertices if vg.index in [i.group for i in vert.groups] and vert.select == True]						
						for i in cont:
							ind.append(i.index)
						if ind:
							for v in ind:
								if self.mode == 'SUBTRACT':
									if vg.weight(v) - value < 0.012:
										vg.add([v], round(0.012, 3), 'REPLACE')
										# print(round(vg.weight(v), 3))
										# print(min_weight)
									else: 
										vg.add([v], round(value, 3), self.mode)
								else:
									vg.add([v], round(value, 3), self.mode)

								#print(round(vg.weight(v), 3))
															
								#	vg.add([v], round(min_weight, 3), 'REPLACE')
								# else:
								# 	self.report({'WARNING'}, ('Vertex' + '"' + str(v) + '"' + ' is not in the group'))				
											
					else:
						self.report({'WARNING'}, ('Nothing changed.' + '"' + vg.name + '"' + ' is locked.'))			 
			go_back_to_initial_mode(self, mode)
			
		else:
			self.report({'WARNING'}, 'Skinned Mesh is not found!')		

		return {'FINISHED'}

class TenfoldWeightBar(Operator):
	bl_idname = "view3d.tenfold_weight"
	bl_label = "Increase/Decrease vertex_weight UI value"
	bl_description = "Increase/Decrease vertex_weight UI value"
	bl_options = {'REGISTER', 'UNDO'}

	value:  bpy.props.FloatProperty(options={'HIDDEN'})
	

	def execute(self, context):
		bpy.data.scenes["Scene"].vertex_weight_input = bpy.data.scenes["Scene"].vertex_weight_input * self.value		
		return  {'FINISHED'}

	
class ClampNearZeroValues(Operator):
	bl_idname = "object.clamp_near_zero_values"
	bl_label = "Clamp Near Zero Values in All Vertex Groups"
	bl_description = "Zero out values less than 0.004 in All Vertex Groups"
	bl_options = {'REGISTER', 'UNDO'}

	@classmethod
	def poll(cls, context):
		return _class_method_mesh_(cls, context)
	
	def execute(self, context):
		if bpy.context.scene.active_mesh in bpy.data.objects:
			obj = bpy.data.objects[bpy.context.scene.active_mesh]
			mode = bpy.context.mode

			bones = get_bones(self)
			bones_names = []
			for b in bones:
				bones_names.append(b.name)

			if bpy.context.mode != 'OBJECT':
				bpy.ops.object.mode_set(mode = 'OBJECT')			

			if obj:
				vgs = obj.vertex_groups			
				if vgs:					
					for vg in vgs:
						if vg.name in bones_names:
							# vertex indices
							ind = []

							# vertex group's content
							cont = [vert for vert in obj.data.vertices if vg.index in [i.group for i in vert.groups]]
						
							for i in cont:
								ind.append(i.index)					
						
							if ind:
								n = 0
								for v in ind:
									value = vg.weight(v)								
									if 0.0 < value < 0.004:
										vg.add([v], 0.0, 'REPLACE')
										n += 1						
								if n > 0:
									self.report({'INFO'}, (vg.name + ": " + str(n) + " values set to 0.0"))
								#else:
								#	self.report({'INFO'}, (vg.name + ": " +  ' Pass'))
						else:
							self.report({'INFO'}, (vg.name + " missed because it has no bones"))

			# original mode
			go_back_to_initial_mode(self, mode)
		
		else:
			self.report({'WARNING'}, 'Skinned Mesh is not found!')	

		return {'FINISHED'}

class DrawBrushTemplateSettings1(Operator):
	bl_label = "Weight Paint Settings 1"
	bl_idname = "brush.draw_brush_template_settings_1"
	bl_description = "Use preset settings. Auto Normalize = 'True', Falloff = 'Constant', Falloff Shape = 'PROJECTED', Lock Relative = 'True', Restrict = 'True'"
	bl_options = {'REGISTER', 'UNDO'}

	def execute(self, context):

		draw_brush = bpy.data.brushes["Draw"]
		if draw_brush.curve_preset != 'CONSTANT':
			draw_brush.curve_preset = 'CONSTANT'

		if draw_brush.falloff_shape != 'PROJECTED':
			draw_brush.falloff_shape = 'PROJECTED'

		blur_brush = bpy.data.brushes["Blur"]
		if blur_brush.curve_preset != 'CONSTANT':
			blur_brush.curve_preset = 'CONSTANT'

		if blur_brush.falloff_shape != 'PROJECTED':
			blur_brush.falloff_shape = 'PROJECTED'

		average_brush = bpy.data.brushes["Average"]
		if average_brush.curve_preset != 'CONSTANT':
			average_brush.curve_preset = 'CONSTANT'

		if average_brush.falloff_shape != 'PROJECTED':
			average_brush.falloff_shape = 'PROJECTED'

		if bpy.context.scene.tool_settings.use_auto_normalize == False:
			bpy.context.scene.tool_settings.use_auto_normalize = True

		if bpy.context.scene.tool_settings.use_lock_relative == False:
				bpy.context.scene.tool_settings.use_lock_relative = True		

		# if draw_brush.use_frontface == False:
		# 	draw_brush.use_frontface = True

		if bpy.context.scene.tool_settings.weight_paint.use_group_restrict == False:
			bpy.context.scene.tool_settings.weight_paint.use_group_restrict = True

		return {'FINISHED'}

class DrawBrushTemplateSettings2(Operator):
	bl_label = "Weight Paint Settings 2"
	bl_idname = "brush.draw_brush_template_settings_2"
	bl_description = "Use preset settings. Auto Normalize = 'True', Falloff = 'Constant', Falloff Shape = 'PROJECTED', Lock Relative = 'False', Restrict = 'False'"
	bl_options = {'REGISTER', 'UNDO'}

	def execute(self, context):

		draw_brush = bpy.data.brushes["Draw"]
		if draw_brush.curve_preset != 'CONSTANT':
			draw_brush.curve_preset = 'CONSTANT'

		if draw_brush.falloff_shape != 'PROJECTED':
			draw_brush.falloff_shape = 'PROJECTED'

		blur_brush = bpy.data.brushes["Blur"]
		if blur_brush.curve_preset != 'CONSTANT':
			blur_brush.curve_preset = 'CONSTANT'

		if blur_brush.falloff_shape != 'PROJECTED':
			blur_brush.falloff_shape = 'PROJECTED'

		average_brush = bpy.data.brushes["Average"]
		if average_brush.curve_preset != 'CONSTANT':
			average_brush.curve_preset = 'CONSTANT'

		if average_brush.falloff_shape != 'PROJECTED':
			average_brush.falloff_shape = 'PROJECTED'

		if bpy.context.scene.tool_settings.use_auto_normalize == False:
			bpy.context.scene.tool_settings.use_auto_normalize = True

		if bpy.context.scene.tool_settings.use_lock_relative == True:
				bpy.context.scene.tool_settings.use_lock_relative = False		

		if draw_brush.use_frontface == True:
			draw_brush.use_frontface = False

		if bpy.context.scene.tool_settings.weight_paint.use_group_restrict == True:
			bpy.context.scene.tool_settings.weight_paint.use_group_restrict = False
		
		if bpy.context.object.data.use_paint_mask_vertex == False:
			bpy.context.object.data.use_paint_mask_vertex = True


		return {'FINISHED'}

class ToggleDrawBrushAddSub(Operator):
	bl_label = "Toggle between Draw Brush Add and Sub"
	bl_idname = "brush.toggle_draw_brush_add_sub"
	bl_description = "Toggle between Draw Brush Add and Sub blend types"
	bl_options = {'REGISTER', 'UNDO'}

	@classmethod
	def poll(cls, context):
		return _class_method_mesh_and_armature_(cls, context)
	
	def execute(self, context):
		bpy.ops.wm.tool_set_by_id(name="builtin_brush.Draw")
		draw_brush = bpy.data.brushes["Draw"]

		brush = bpy.context.tool_settings.weight_paint.brush
		if brush != 'Draw':
			bpy.context.tool_settings.weight_paint.brush = draw_brush

		if draw_brush.blend == 'ADD':
			draw_brush.blend = 'SUB'
			# self.report({'INFO'},  "SUB")
		else:
			draw_brush.blend = 'ADD'
			# self.report({'INFO'},  "ADD")
		
		return {'FINISHED'}

class PickActiveMesh(Operator):
	bl_label = ""
	bl_idname = "object.pick_active_mesh"
	bl_description = "Pick Active Mesh"
	bl_options = {'REGISTER', 'UNDO'}

	@classmethod
	def poll(cls, context):
		return context.object is not None
	
	def execute(self, context):
		obj = bpy.context.object
		if bpy.context.object.type == 'MESH':
			bpy.context.scene.active_mesh = obj.name
		
		return {'FINISHED'}

class WeightPaintModeOn(Operator):
	bl_label = "Weight Paint Mode"
	bl_idname = "object.weight_paint_mode_on"
	bl_description = "Weight Paint Mode"
	bl_options = {'REGISTER', 'UNDO'}

	@classmethod
	def poll(cls, context):
		return _class_method_mesh_and_armature_(cls, context)
	
	def execute(self, context):
		am = bpy.context.scene.active_mesh
		if am != "":
			if am in bpy.data.objects:
				obj = bpy.data.objects[bpy.context.scene.active_mesh]
				
				if obj.data.use_paint_mask_vertex == False:
					obj.data.use_paint_mask_vertex = True

				mode = bpy.context.mode				
				
				if mode != 'PAINT_WEIGHT':	
					# activate brush
					brush = bpy.context.tool_settings.weight_paint.brush
					if brush != "Draw":
						bpy.context.tool_settings.weight_paint.brush = bpy.data.brushes["Draw"]

					#deselect
					sel = bpy.context.selected_objects[:]
					if len(sel):
						for i in sel:
							i.select_set(False)			
					
					obj.select_set(True)
					bpy.context.view_layer.objects.active = obj
					bpy.ops.object.mode_set(mode='WEIGHT_PAINT')				
					
					# lock and select
					#lock_and_select(self, obj)

					# if carpaint material is on
					if bpy.context.space_data.type == 'VIEW_3D':
						if bpy.context.space_data.shading.studio_light == 'metal_carpaint.exr':
							bpy.context.space_data.shading.studio_light = 'basic_1.exr'
			else:
				self.report({'WARNING'},  am + " was not found.")
		else:
			self.report({'WARNING'}, "Pick the Mesh for skinning.")
		
		return {'FINISHED'}

class ObjectEditModeOn(Operator):
	bl_label = "Object/Edit Mode On"
	bl_idname = "object.object_edit_mode_on"
	bl_description = "Object/Edit Mode"
	bl_options = {'REGISTER', 'UNDO'}
	mode: bpy.props.StringProperty(name = "Mode", options = {'HIDDEN'})

	@classmethod
	def poll(cls, context):
		return context.object is not None

	def execute(self, context):
		obj = bpy.context.object
		if obj.hide_get() == False and obj.hide_select == False and obj.hide_viewport == False:
			obj_type = bpy.context.object.type
			current_mode = bpy.context.mode
			noedit_types = ['EMPTY','VOLUME','LIGHT','LIGHT_PROBE','CAMERA','SPEAKER']
			if obj_type not in noedit_types:
				if self.mode != current_mode and (self.mode + '_MESH') != current_mode:				
					bpy.ops.object.mode_set(mode = self.mode)
					if bpy.context.scene.lock_all_unused_vgs:
						bpy.ops.object.lock_unused_vgs()			
			else:
				self.report({'WARNING'},  "Nothing changed.")
		else:
			self.report({'WARNING'}, ('Mode Change failed. The context object is hidden or locked!'))		

		return {'FINISHED'}

class PoseModeOn(Operator):
	bl_label = "Pose Mode"
	bl_idname = "object.pose_mode_on"
	bl_description = "Pose Mode"
	bl_options = {'REGISTER', 'UNDO'}

	@classmethod
	def poll(cls, context):
		return _class_method_mesh_and_armature_(cls, context)
	
	def execute(self, context):		
		if bpy.context.mode != 'POSE':
			if "Armature" in bpy.data.objects[bpy.context.scene.active_mesh].modifiers:						
				bpy.context.view_layer.objects.active = bpy.data.objects[bpy.context.scene.active_mesh].modifiers['Armature'].object
				bpy.ops.object.mode_set(mode='POSE')
			if bpy.context.scene.lock_all_unused_vgs:
				bpy.ops.object.lock_unused_vgs()

		return {'FINISHED'}

class ToggleWeightPoseModes(Operator):
	bl_label = "Toggle between Weight and Pose Modes"
	bl_idname = "object.toggle_weight_pose_modes"
	bl_description = "Toggle between Weight and Pose Modes"
	bl_options = {'REGISTER', 'UNDO'}

	@classmethod
	def poll(cls, context):
		return _class_method_mesh_and_armature_(cls, context)
	
	def weight_paint_mode(self):
		bpy.ops.object.weight_paint_mode_on()		 
		brush = bpy.context.tool_settings.weight_paint.brush
		if brush != 'Draw':
			bpy.context.tool_settings.weight_paint.brush = bpy.data.brushes["Draw"]

	def execute(self, context):			
		mode = bpy.context.mode
		if mode == 'PAINT_WEIGHT':
			bpy.ops.object.pose_mode_on()
			# self.report({'INFO'},  'POSE MODE')
		elif mode == 'POSE':
			self.weight_paint_mode()
			# self.report({'INFO'},  'WEIGHT PAINT MODE')
			
		else:
			self.weight_paint_mode()
			# self.report({'INFO'},  'WEIGHT PAINT MODE')
		
		return {'FINISHED'}

class LockUnusedVGs (Operator):
	bl_label = "Unlock Active VGs"
	bl_idname = "object.lock_unused_vgs"
	bl_description = "Unlock active Vertex Group, lock others except for Root"
	
	@classmethod
	def poll(cls, context):
		return context.object is not None
	
	def execute(self, context):
		obj = bpy.context.object	
		lock_unused(self, obj)
		#else:
		#	self.report({'WARNING'}, (self.bl_label + ": " + 'This object must be a Skinned Mesh for this action'))
		
		return {'FINISHED'}

class SelectActiveMesh (Operator):
	bl_label = "Select Skinned Mesh"
	bl_idname = "object.select_skinned_mesh"
	bl_description = "Select Skinned Mesh"
	mode: bpy.props.StringProperty()

	@classmethod
	def poll(cls, context):
		return _class_method_mesh_(cls, context)
	
	def execute(self, context):

		if bpy.context.scene.active_mesh in bpy.data.objects:
			obj = bpy.data.objects[bpy.context.scene.active_mesh]			
			
			obj.select_set(True)
			bpy.context.view_layer.objects.active = obj
			bpy.ops.object.object_edit_mode_on(mode=self.mode)
		
		return {'FINISHED'}

classes = (
	#VertexAssignController,
	GenerateRig,	
	AddArmatureMod,
	ScaleAllBones,
	SyncVG,
	#FillAllVG,
	FillActiveVG,
	DrawBrushBlendToggle,
	DrawBrushTemplateSettings1,
	DrawBrushTemplateSettings2,
	ToggleDrawBrushAddSub,	
	PickActiveMesh,
	WeightPaintModeOn,
	PoseModeOn,
	ToggleWeightPoseModes,
	ObjectEditModeOn,
	ShiftVertexWeights,
	StateEditPoseWPButtons,
	ClampNearZeroValues,
	SelectBonesAndMode,
	SelectVGtoBone,
	LockUnusedVGs,
	SelectActiveMesh,
	TenfoldWeightBar	
)

# Functions
					
def update_selection(cls):
	bpy.ops.object.object_edit_mode_on(mode="EDIT")
	bpy.ops.object.object_edit_mode_on(mode="OBJECT")
	bpy.ops.object.object_edit_mode_on(mode="EDIT")

def go_back_to_initial_mode(cls, mode):
	if mode != "" and mode != "EDIT_ARMATURE":		
		if mode == 'PAINT_WEIGHT':
			mode = 'WEIGHT_PAINT'		
		elif mode == 'EDIT_MESH':
			mode = 'EDIT'
		bpy.ops.object.mode_set(mode = mode)

def lock_and_select(cls, obj):
	# lock unused vertex groups and select active
	if "Armature" in obj.modifiers:
		armature = obj.modifiers['Armature'].object
		active_bone = None
		if armature.data.bones.active is not None:
			active_bone = armature.data.bones.active

		if active_bone:
			# lock unused
			if bpy.context.scene.lock_all_unused_vgs:
				if active_bone:
					for vg in obj.vertex_groups[:]:
						if vg.name != 'Root' and vg.name != active_bone.name:					
							vg.lock_weight = True
						else:
							vg.lock_weight = False

			# select bone's vertex group						
			if bpy.context.scene.select_all_vg_vertices:
				vgs = obj.vertex_groups[:]
				vgs_namelist = []
				for i in vgs:
					vgs_namelist.append(i.name)
					
				if active_bone.name in vgs_namelist:
					bpy.ops.paint.vert_select_all(action='DESELECT')
					bpy.ops.object.vertex_group_set_active(group = active_bone.name)
					bpy.ops.object.vertex_group_select()
				else:
					bpy.ops.paint.vert_select_all(action='DESELECT')
					cls.report({'WARNING'}, 'Vertex Group connected to the active Bone is not found!')
		else:
			cls.report({'WARNING'}, 'No Active Bone! Lock failed!')

def add_armature(cls):
	obj = bpy.context.object
	if obj.type == 'MESH':
		length = bpy.context.scene.bone_length
		
		if  length is not None:
			length = length*100			
		else:
			length = 0.1
		
		if bpy.context.mode != 'OBJECT':
			bpy.ops.object.object_edit_mode_on(mode="OBJECT")

		# add armature
		bpy.ops.object.armature_add(radius = length)

		armature = bpy.context.scene.objects[-1].data
		armature.show_names = True		
		armature.bones[0].name = 'Root'

		#add modifier		
		if 'Armature' not in obj.modifiers:
			bpy.ops.object.mode_set(mode = 'OBJECT')
			bpy.context.view_layer.objects.active = obj
			bpy.ops.object.modifier_add(type='ARMATURE')
			obj.modifiers['Armature'].object =  bpy.context.scene.objects[-1]
		else:		
			#cls.report({'WARNING'}, ("This mesh already has Armature Modifier"))		
			if obj.modifiers['Armature'].object is None:				
				obj.modifiers['Armature'].object =  bpy.context.scene.objects[-1]
				cls.report({'INFO'}, ("Armature Object added"))

		#bpy.context.view_layer.objects.active = obj
		#obj.select_set(True)

		# sync
		bpy.context.view_layer.objects.active = obj
		bpy.ops.object.sync_vg()

		# set 1.0 to Root
		weight = bpy.context.scene.tool_settings.vertex_group_weight
		bpy.context.scene.tool_settings.vertex_group_weight = 1
		bpy.ops.object.mode_set(mode = 'EDIT')
		for vg in obj.vertex_groups[:]:
			if vg.name == 'Root':
				obj.vertex_groups.active = vg
		bpy.ops.mesh.select_all(action='SELECT')
		bpy.ops.object.vertex_group_assign()
		bpy.context.scene.tool_settings.vertex_group_weight = weight
		bpy.ops.object.mode_set(mode = 'OBJECT')



def get_bones(cls):	
	if bpy.context.object is not None and 'Armature' in bpy.context.object.modifiers and bpy.context.object.modifiers["Armature"].object is not None or bpy.data.objects[bpy.context.scene.active_mesh].modifiers["Armature"].object is not None:
		bones = None
		if bpy.context.object.type != "MESH":
			bones = bpy.data.objects[bpy.context.scene.active_mesh].modifiers["Armature"].object.data.bones[:]
		else:
			bones = bpy.context.object.modifiers["Armature"].object.data.bones[:]
		if bones is not None:
			return bones
		else:
		   return None

def set_properties_to_data(cls):
	screen = bpy.context.screen
	areas = bpy.context.screen.areas[:]
	area_list = [area.type == 'PROPERTIES' for area in areas]

	k=0
	for index in area_list:
		if index:
			break		
		else:
			k += 1
	
	if areas[k].regions.data.spaces.active.context != 'DATA':		
		areas[k].regions.data.spaces.active.context = 'DATA'

def lock_unused(cls, obj):
	# lock unused								
	if obj:
		if obj.vertex_groups:
			active = obj.vertex_groups.active
			if active.name != 'Root':
				for vg in obj.vertex_groups[:]:
					if vg.name != 'Root' and vg.name != active.name:					
						if vg.lock_weight == False:
							vg.lock_weight = True
					else:
						vg.lock_weight = False

def _class_method_mesh_(cls, context):
	if bpy.context.scene.active_mesh !='' and bpy.context.object is not None:
		if bpy.context.scene.active_mesh in bpy.data.objects:
			mesh = bpy.data.objects[bpy.context.scene.active_mesh]
			if mesh.hide_get() == False and mesh.hide_select == False and mesh.hide_viewport == False:
				return True

def _class_method_armature_(cls, context):
	if bpy.context.object is not None and "Armature" in bpy.context.object.modifiers and bpy.context.object.modifiers["Armature"].object is not None:
		armature = bpy.context.object.modifiers["Armature"].object
		if armature.hide_get() == False and armature.hide_select == False and armature.hide_viewport == False:
			return True

def _class_method_mesh_and_armature_(cls, context):
	if bpy.context.object is not None and bpy.context.scene.active_mesh !='' and bpy.context.scene.active_mesh in bpy.data.objects and 'Armature' in bpy.data.objects[bpy.context.scene.active_mesh].modifiers is not None and bpy.data.objects[bpy.context.scene.active_mesh].modifiers['Armature'].object is not None:
		mesh = bpy.data.objects[bpy.context.scene.active_mesh]
		armature = mesh.modifiers['Armature'].object
		if armature.hide_get() == False and armature.hide_select == False and armature.hide_viewport == False and mesh.hide_get() == False and mesh.hide_select == False and mesh.hide_viewport == False:
			return True

def register():
	for cls in classes:
		bpy.utils.register_class(cls)

	bpy.types.Scene.bone_length = bpy.props.FloatProperty(
		name="Scale",
		default = 0.1,
		soft_min = 0.0,
		soft_max = 1.0,
		min = 0.0,
		max = 1.0
		)
	bpy.types.Scene.vertex_weight_input = bpy.props.FloatProperty(
		name="Value",
		default = 0.004,		
		min = 0.00,
		max = 1.0,
		step = 0.4,
		precision = 3
		)	
	bpy.types.Scene.active_mesh = bpy.props.StringProperty(
		default = "",
		name = ""
		)
	bpy.types.Scene.select_all_vg_vertices = bpy.props.BoolProperty(
		name="Select",
		description = "Always select All Vertex Group Vertices in Weight Paint Mode.",
		default = True
		)
	bpy.types.Scene.lock_all_unused_vgs = bpy.props.BoolProperty(
		name="Lock",
		description = "Always Lock Vertex Groups that are not Root or Active VG.",
		default = True
		)
	bpy.types.Scene.auto_add_vertex_group = bpy.props.BoolProperty(
		name="Auto Sync VG",
		description = "Always generate a Vertex Group when a new Bone is added.",
		default = True
		)
	bpy.types.Scene.weight_paint_mode = bpy.props.BoolProperty()

	bpy.types.Scene.weight_paint_on_off = bpy.props.BoolProperty(
		name="WP",
		description = "Select Weight Paint Mode",
		default = False
		)

	bpy.types.Scene.pose_on_off = bpy.props.BoolProperty(
		name="POSE",
		description = "Select Pose Mode",
		default = False
		)

	bpy.types.Scene.edit_on_off = bpy.props.BoolProperty(
		name="EDIT",
		description = "Select Edit Mode",
		default = False
	)

	bpy.types.Scene.vert_assign_mode_enum = bpy.props.EnumProperty(
	name="",
	description="Vertex Assign Mode",
	items=[('ADD', 'ADD', ''), ('SUBTRACT', 'SUBTRACT', ''), ('REPLACE', 'REPLACE', '')]
	)

def unregister():
	for cls in reversed(classes):
		bpy.utils.unregister_class(cls)
	bpy.types.Scene.vert_assign_mode_enum 	
	bpy.types.Scene.bone_length
	bpy.types.Scene.vertex_weight_input
	bpy.types.Scene.active_mesh
	bpy.types.Scene.select_all_vg_vertices
	bpy.types.Scene.lock_all_unused_vgs
	bpy.types.Scene.auto_add_vertex_group
	bpy.types.Scene.weight_paint_mode
	bpy.types.Scene.weight_paint_on_off
	bpy.types.Scene.pose_on_off
	bpy.types.Scene.edit_on_off	
	


