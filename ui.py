import bpy
from bpy.utils import register_class, unregister_class
from bpy.types import Panel, Menu, Operator
from . modeling import *
from . generators import *
from . rigging_skinning import *
from . export import *
import webbrowser

# Main Panels
class ModelingPanel(Panel):
	bl_label = "Modeling"
	bl_idname = "OBJECT_PT_AUT_MODELING_PANEL"
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = "Automation Tools"
	bl_options =  {'DEFAULT_CLOSED'}

	def draw(self, context):
		layout = self.layout

class ExportPanel(Panel):
	bl_label = "Export"
	bl_idname = "OBJECT_PT_AUT_EXPORT_PANEL"
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = "Automation Tools"
	bl_options =  {'DEFAULT_CLOSED'}

	def draw(self, context):
		layout = self.layout
		column = layout.column()
		column.label(text = 'File Path:')
		column.prop(bpy.context.scene, "export_path")
		column.prop(bpy.context.scene, "if_apply_transform")
		column.prop(bpy.context.scene, "if_move_to_origin")

class BackupPanel(Panel):
	bl_label = "Backup"
	bl_idname = "OBJECT_PT_AUT_BACKUP_PANEL"
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = "Automation Tools"
	bl_options =  {'DEFAULT_CLOSED'}

	def draw(self, context):
		layout = self.layout
		column = layout.column()		
		column.prop(bpy.context.scene, "at_backup_path")

class GeneratorsPanel(Panel):
	bl_label = "Generators"
	bl_idname = "OBJECT_PT_AUTOMATION_TOOLS_GENERATORS_PANEL"
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = "Automation Tools"
	bl_options =  {'DEFAULT_CLOSED'}

	def draw(self, context):
		layout = self.layout

# class UtilsPanel(Panel):
# 	bl_label = "Utils"
# 	bl_idname = "OBJECT_PT_AUTOMATION_TOOLS_UTILS_PANEL"
# 	bl_space_type = 'VIEW_3D'
# 	bl_region_type = 'UI'
# 	bl_category = "Automation Tools"
# 	bl_options =  {'DEFAULT_CLOSED'}

# 	def draw(self, context):
# 		layout = self.layout

class RiggingSkinningPanel(Panel):
	bl_label = "Rigging/Skinning"
	bl_idname = "OBJECT_PT_AUT_RIGGING_SKINNING_PANEL"
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = "Automation Tools"
	bl_options =  {'DEFAULT_CLOSED'}

	def draw(self, context):
		layout = self.layout

# Sub Panels
class ActiveMeshPanel(Panel):
	bl_label = "Active Mesh"
	bl_idname = "OBJECT_PT_AUT_RIG_SK_PANEL_SKINNED_MESH"
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = "Automation Tools"
	bl_options =  {'DEFAULT_CLOSED'}

	def draw(self, context):
		scene = bpy.context.scene
		layout = self.layout
		column = layout.column(align=True)

		split = column.split(factor=0.75, align=True)
		split.prop(bpy.context.scene, 'active_mesh')

		split.operator("object.pick_active_mesh", icon='EYEDROPPER')
		column.operator(SelectActiveMesh.bl_idname, text = "Select").mode='EDIT'
		column.separator()
		column.operator("OBJECT_OT_at_wiki", text = "Help", icon = "HELP").tool = 'active_mesh'

class NamesPanel(Panel):
	bl_label = "Names"
	bl_idname = "OBJECT_PT_automation_tools_naming_panel"
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = "Automation Tools"
	bl_options =  {'DEFAULT_CLOSED'}
	bl_parent_id = ModelingPanel.bl_idname

	def draw(self, context):
		layout = self.layout
		column = layout.column(align=True)

		if bpy.context.object is not None:
			column.label(text="Object:")
			# column.prop(bpy.context.object, 'name', text='')
			split = column.split(factor=0.8, align=True)
			split.prop(bpy.context.scene, 'new_object_name_input', text='')
			split.operator(AutomationRename_CopyName.bl_idname, text = '', icon='TRIA_DOWN').target='OBJECT'		
			remane_obj = column.operator(AutomationRename.bl_idname, text = 'Rename')
			remane_obj.target='OBJECT'
			remane_obj.new_name=context.scene.new_object_name_input
			column.separator(factor=1.0)

		if bpy.context.collection is not None:
			column.label(text="Collection:")
			# column.prop(bpy.context.collection, 'name', text='')
			split = column.split(factor=0.8, align=True)
			split.prop(bpy.context.scene, 'new_collection_name_input', text='')
			split.operator(AutomationRename_CopyName.bl_idname, text = '', icon='TRIA_DOWN').target='COLLECTION'

			rename_collection = column.operator(AutomationRename.bl_idname, text = 'Rename')
			rename_collection.target='COLLECTION'
			rename_collection.new_name = context.scene.new_collection_name_input

			column.separator(factor=1.0)		

		column.label(text="Object & Data:")
		if context.object:
			column.template_ID(context.view_layer.objects, "active")
			if context.object.data:	
				column.template_ID(context.object, 'data')
		column.operator(CopyObjectNameToDataName.bl_idname, text = "Sync")
		column.operator(FindDataUsers.bl_idname, text = "Find Users")
		column.separator(factor=1.0)

		column.label(text="Fix:")
		column.operator("object.name_with_spaces", text = "Object")
		column.operator("outliner.name_with_spaces", text = "Collection")
		
		column.operator(RemoveDuplicates.bl_idname, text = "Materials").collection = 0
		column.operator(RemoveDuplicates.bl_idname, text = "Images").collection = 1
		column.operator(RemoveDuplicates.bl_idname, text = "Meshes").collection = 2

		column.operator(ObjectNameRemoveSpaces.bl_idname, text = "Remove Spaces")
		column.operator(FixUVMapName.bl_idname, text = "UVMap")
		column.separator(factor=1.0)

		column.label(text="Copy/Paste:")
		column.operator("object.copy_object_name", text = "Copy")
		column.operator("object.paste_object_name", text = "Paste")
		column.operator(SwapObjectNames.bl_idname, text = "Swap")

		if context.active_object is not None:
			transfer_btn = column.operator(AutomationRename.bl_idname, text = "Transfer")
			transfer_btn.new_name=context.active_object.name
			transfer_btn.target='OBJECT'

		column.separator(factor=1.0)
		column.label(text="Bake:")
		column.operator("object.rename_lp_hp", text = "Low/High-poly")
		
		column.separator(factor=1.0)

		column.label(text="Numerate:")
		column.operator(AT_Numerate.bl_idname, text = 'Numerate')		
		column.operator(AT_NumerateOrdered.bl_idname, text = 'Numerate Ordered')
		column.operator(AT_NumerateLODsOrdered.bl_idname, text = 'Numerate LODs Ordered')		
		
		column.separator(factor=1.0)

class UVsPanel(Panel):
	bl_label = "UVs"
	bl_idname = "OBJECT_PT_automation_tools_uvs_panel"
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = "Automation Tools"
	bl_options =  {'DEFAULT_CLOSED'}
	bl_parent_id = ModelingPanel.bl_idname

	def draw(self, context):
		layout = self.layout

class LightsUVsPanel(Panel):
	bl_label = "Lights"
	bl_idname = "OBJECT_PT_automation_tools_lights_panel"
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = "Automation Tools"
	bl_options =  {'DEFAULT_CLOSED'}
	bl_parent_id = UVsPanel.bl_idname

	def draw(self, context):
		layout = self.layout
		column = layout.column(align=True)

		column.operator("uv.reset", text = "Facets")

		flt = column.operator("object.lights_unwrap", text = "Flat")
		flt.U = 0.0
		flt.V = 1.0

		strp = column.operator("object.lights_unwrap", text = "Stripes")
		strp.U = 0.0
		strp.V = 0.0

		blb = column.operator("object.lights_unwrap", text = "Bulb")
		blb.U = 0.5
		blb.V = 0.5

		column.operator("OBJECT_OT_at_wiki", text = "Help", icon = "HELP").tool = 'uvs_lights'

class BodyUVs(Panel):
	bl_label = "Body"
	bl_idname = "OBJECT_PT_automation_tools_body_uvs_panel"
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = "Automation Tools"
	bl_options =  {'DEFAULT_CLOSED'}
	bl_parent_id = UVsPanel.bl_idname

	def draw(self, context):
		layout = self.layout
		column = layout.column(align=True)

		column.operator("mesh.snap_bottom_uvs", text = "Snap Body Bottom Uvs")

class UVToolsPanel(Panel):
	bl_label = "UV Tools"
	bl_idname = "OBJECT_PT_automation_tools_uv_tools_panel"
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = "Automation Tools"
	bl_options =  {'DEFAULT_CLOSED'}
	bl_parent_id = UVsPanel.bl_idname

	def draw(self, context):
		layout = self.layout
		column = layout.column(align=True)

		column.label(text="UV Seams:")
		column.operator(UVSeamsFromHardEdges.bl_idname, text = "Hard edges > UV Seams")
		column.operator(UnwrapCylinder.bl_idname, text = "Cylinder")

		column.label(text="Unwrap:")
		column.operator(AT_UVUnwrap.bl_idname, text = "UVUnwrap")
		column.prop(context.scene, 'apply_uv_scale', text = "Set UV Scale")

		#column.operator(UnwrapCylinder.bl_idname, text = "Pipe")
		column.prop(bpy.context.scene, "texel_value", text = 'Texel Density:')
		column.operator(ScaleUVs.bl_idname, text = "Get").command = "GET"
		column.operator(ScaleUVs.bl_idname, text = "Set").command = "SET"

		column.label(text="UV Checker:")
		column.operator(CreateUVChecker.bl_idname, text = "Add")
		split = column.split(factor=0.5, align=True)
		split.operator(ToggleUVChecker.bl_idname, text = "Show").action = False
		split.operator(ToggleUVChecker.bl_idname, text = "Hide").action = True

		if context.object is not None and context.object.active_material is not None:
			column.prop(bpy.context.scene, 'checker_scale', text = "Scale")

		column.label(text="UV Rotate/Mirror:")
		split = column.split(factor=0.5, align=True)
		split.operator(UVRotate.bl_idname, text = "Rotate +90").angle = 1.5708
		split.operator(UVRotate.bl_idname, text = "Rotate -90").angle = -1.5708

		split = column.split(factor=0.5, align=True)
		split.operator(UVMirror.bl_idname, text = "Mirror X").axis = (True, False, False)
		split.operator(UVMirror.bl_idname, text = "Mirror Y").axis = (False, True, False)

class GeometryPanel(Panel):
	bl_label = "Geometry"
	bl_idname = "OBJECT_PT_AUT_geometry_panel"
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = "Automation Tools"
	bl_options =  {'DEFAULT_CLOSED'}
	bl_parent_id = ModelingPanel.bl_idname

	def draw(self, context):
		layout = self.layout

class MaterialsPanel(Panel):
	bl_label = "Materials"
	bl_idname = "OBJECT_PT_automation_tools_materials_panel"
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = "Automation Tools"
	bl_options =  {'DEFAULT_CLOSED'}
	bl_parent_id = ModelingPanel.bl_idname

	def draw(self, context):
		layout = self.layout

class MaterialsAddPanel(Panel):
	bl_label = "Generate"
	bl_idname = "OBJECT_PT_automation_tools_materials_generate_panel"
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = "Automation Tools"
	bl_options =  {'DEFAULT_CLOSED'}
	bl_parent_id = MaterialsPanel.bl_idname

	def draw(self, context):
		layout = self.layout
		column = layout.column(align=False)
		column.operator("object.add_body_materials", text = "Body Mats")
		column.operator("object.add_fixture_materials", text = "Fixture Mats")
		column.operator("object.generate_id_colors", text = "Random IDs")

class RimGeneratorPanel(Panel):
	bl_label = "Base Rim"
	bl_idname = "OBJECT_PT_automation_tools_rim_generator_panel"
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = "Automation Tools"
	bl_options =  {'DEFAULT_CLOSED'}
	bl_parent_id = GeneratorsPanel.bl_idname

	def draw(self, context):
		layout = self.layout
		column = layout.column(align=True)
		column.operator("OBJECT_OT_rim_generator", text = "New Rim Project", icon = 'ADD')
		column.operator("object.add_bevel_width_driver", text = 'Lerp Bevel Width', icon = 'MOD_BEVEL')
		column.operator("object.add_empty_shape_keys", text = "Add Empty Shape Keys", icon = 'SHAPEKEY_DATA').type = 'RIM'
		column.separator()
		column.operator("OBJECT_OT_at_wiki", text = "Help", icon = "HELP").tool = "rim_generator"

class MaterialsCleanupPanel(Panel):
	bl_label = "Cleanup"
	bl_idname = "OBJECT_PT_automation_tools_materials_cleanup_panel"
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = "Automation Tools"
	bl_options =  {'DEFAULT_CLOSED'}
	bl_parent_id = MaterialsPanel.bl_idname

	def draw(self, context):
		layout = self.layout
		column = layout.column(align=True)

		column.label(text = 'Mesh:')
		column.operator("object.cleanup_unused_mesh_mats", text = "Unused")
		column.operator("object.delete_all_mesh_mats", text = "All")

		column.label(text = 'Scene:')
		column.operator("object.cleanup_mats_scene_unused", text = "Unused")
		column.operator("object.cleanup_mats_scene_all", text = "All")

class MaterialsEditPanel(Panel):
	bl_label = "Edit"
	bl_idname = "OBJECT_PT_automation_tools_materials_edit_panel"
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = "Automation Tools"
	bl_options =  {'DEFAULT_CLOSED'}
	bl_parent_id = MaterialsPanel.bl_idname

	def draw(self, context):
		layout = self.layout
		column = layout.column(align=True)

		column.label(text = 'Add/Replace:')
		split = column.split(factor=0.8, align=True)
		split.prop(bpy.context.scene, 'src_mat', text = 'Source')
		split.operator(ReplaceMaterialsGetter.bl_idname, text = "Get").mat = 'src'
		split.operator(ReplaceMaterialsAdder.bl_idname, text = "Add").mat = 'add_src'

		split = column.split(factor=0.8, align=True)
		split.prop(bpy.context.scene, 'trg_mat', text = 'Target')
		split.operator(ReplaceMaterialsGetter.bl_idname, text = "Get").mat = 'trg'
		split.operator(ReplaceMaterialsAdder.bl_idname, text = "Add").mat = 'add_trg'
		column.operator(ReplaceMaterials.bl_idname, text = "Apply")

		column.label(text = 'Fix Slots')
		column.prop(bpy.context.scene, "json_materials_data_path")
		column.operator("object.fix_material_slots", text = "Fix Slots")

class HierarchyPanel(Panel):
	bl_label = "Hierarchy"
	bl_idname = "OBJECT_PT_automation_tools_hierarchy_panel"
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = "Automation Tools"
	bl_options =  {'DEFAULT_CLOSED'}
	bl_parent_id = ModelingPanel.bl_idname

	def draw(self, context):
		layout = self.layout
		column = layout.column(align=True)

		column.operator("OBJECT_OT_generate_hierarchy", text = "Body").collection_type = 'Body'
		column.operator("OBJECT_OT_generate_hierarchy", text = "Rim").collection_type = 'Rim'
		column.operator("OBJECT_OT_generate_hierarchy", text = "Fixture").collection_type = 'Fixture'		
		column.operator("object.create_group", text = "Group")
		column.operator(CreateCollection.bl_idname, text = "Collection")
		column.operator("OBJECT_OT_generate_hierarchy", text = "LODs").collection_type = 'LODs'

class SocketsPanel(Panel):
	bl_label = "Sockets"
	bl_idname = "OBJECT_PT_automation_tools_sockets_panel"
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = "Automation Tools"
	bl_options =  {'DEFAULT_CLOSED'}
	bl_parent_id = ModelingPanel.bl_idname

	def draw(self, context):
		layout = self.layout
		column = layout.column(align=True)

		column.operator(AddEmptyInComponentSelectionCenter.bl_idname, text = "Selection")
		column.operator(AddEmptyInLoop.bl_idname, text = "Loops")
		column.operator(SocketInObjectPivotPosition.bl_idname, text = "Pivot")
		column.operator(AT_SpawnCollectionInstance.bl_idname, text = "Collection Instance")	

class BonesPanel(Panel):
	bl_label = "Bones"
	bl_idname = "OBJECT_PT_AUT_RIG_SK_BONES_PANEL"
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = "Automation Tools"
	bl_options =  {'DEFAULT_CLOSED'}
	bl_parent_id = RiggingSkinningPanel.bl_idname

	def draw(self, context):
		layout = self.layout
		column = layout.column(align=True)

		#column.operator("object.add_armature_mod", text = "Add Armature")
		column.operator("wm.call_menu", text = "Add Bone", icon='ADD').name = GenerateRigMenu.bl_idname
		split = column.split(factor=0.75, align=True)
		split.prop(bpy.context.scene, 'bone_length', slider = True)
		split.operator("object.scale_all_bones", text = "Apply")
		column.operator("armature.symmetrize", text = "Symmetrize")
		edit_wp_pose_buttons(self, context)
		column.operator("wm.call_menu", text = "Select", icon='MENU_PANEL').name = SelectBonesMenu.bl_idname

class ShapeKeysPanel(Panel):
	bl_label = "Shape Keys"
	bl_idname = "OBJECT_PT_SHAPE_KEYS_PANEL"
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = "Automation Tools"
	bl_options =  {'DEFAULT_CLOSED'}
	bl_parent_id = RiggingSkinningPanel.bl_idname

	@classmethod
	def poll(cls, context):
		return context.object is not None and context.object.type == 'MESH'

	def draw(self, context):
		obj = context.object
		layout = self.layout
		column = layout.column()
		split = layout.split(factor = 0.91)
		column_left = split.column()
		column_left.template_list(
			listtype_name = "UI_UL_list",
			list_id = 'OBJECT_PT_SHAPE_KEYS_PANEL',
			dataptr = context.object.data.shape_keys,
			propname = 'key_blocks',
			active_dataptr = context.object,
			active_propname = 'active_shape_key_index',
			item_dyntip_propname = "Shape Keys"
		)
		column_right = split.column(align=True)
		column_right.operator("object.shape_key_add", text = "", icon = 'ADD').from_mix = False
		column_right.operator("object.shape_key_remove", text = "", icon = 'REMOVE').all = False
		column_right.separator(factor=1.0)
		column_right.operator("wm.call_menu", text = "", icon = 'DOWNARROW_HLT').name = "MESH_MT_shape_key_context_menu"
		column_right.separator(factor=1.0)
		column_right.operator("object.shape_key_move", text = "", icon = 'TRIA_UP').type = 'UP'
		column_right.operator("object.shape_key_move", text = "", icon = 'TRIA_DOWN').type = 'DOWN'		

		if obj.active_shape_key and obj.active_shape_key.name != 'Basis':
			column = layout.column()
			split = column.split(factor = 0.91, align = True)
			split.prop(obj.active_shape_key, 'value', text = "Value", slider = True)

			if obj.active_shape_key.value > 0:
				split.operator("object.toggle_0_1_active_shape_key", text = "", icon = 'RADIOBUT_ON').value = 0.0
			else:
				split.operator("object.toggle_0_1_active_shape_key", text = "", icon = 'RADIOBUT_OFF').value = 1.0

		row = layout.row(align = True)
		row.operator("object.add_empty_shape_keys", text = "Body", icon = 'ADD').type = 'BODY'
		row.operator("object.add_empty_shape_keys", text = "Rim", icon = 'ADD').type = 'RIM'

		column = layout.column()
		column.operator(AT_SetShapeKeysVerts.bl_idname, text = "Set Verts")

class VertexGroupsPanel(Panel):
	bl_label = "Vertex Groups"
	bl_idname = "OBJECT_PT_AUT_RIG_SK_VERTEX_GROUPS_PANEL"
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = "Automation Tools"
	bl_options =  {'DEFAULT_CLOSED'}
	bl_parent_id = RiggingSkinningPanel.bl_idname

	@classmethod
	def poll(cls, context):
		return context.object is not None and context.object.type == 'MESH'

	def draw(self, context):
		obj = bpy.context.object
		layout = self.layout

		col = layout.column()
		split = layout.split(factor = 0.92)
		column_left = split.column()

		column_left.template_list(
			listtype_name = "MESH_UL_vgroups",
			list_id = 'OBJECT_PT_VG_PANEL',
			dataptr = context.object,
			propname = 'vertex_groups',
			active_dataptr = context.object.vertex_groups,
			active_propname = 'active_index',
			item_dyntip_propname = "Vertex Groups"
		)

		column_right = split.column(align=True)
		#column_right.operator("object.vertex_group_add", text = "", icon = '')
		column_right.operator("object.vertex_group_remove", text = "", icon = 'REMOVE')
		column_right.separator(factor=1.0)
		column_right.operator("wm.call_menu", text = "", icon = 'DOWNARROW_HLT').name = "MESH_MT_vertex_group_context_menu"
		column_right.separator(factor=1.0)
		column_right.operator("object.vertex_group_move", text = "", icon = 'TRIA_UP').direction = 'UP'
		column_right.operator("object.vertex_group_move", text = "", icon = 'TRIA_DOWN').direction = 'DOWN'

		if	len(obj.vertex_groups) > 0:
			row = layout.row()
			if obj.vertex_groups.active.lock_weight:
				row.operator(LockUnusedVGs.bl_idname, text = 'Unlock', icon='LOCKED', depress = True)
			else:
				row.operator(LockUnusedVGs.bl_idname, text = 'Unocked', icon='UNLOCKED')

			row.operator("object.select_vg_to_bone", text = "Select Bone", icon='ARMATURE_DATA')
			row = layout.row(align = True)
			row.operator("object.vertex_group_assign", text = "Assign")
			row.operator("object.vertex_group_remove_from", text = "Remove")
			row.separator(factor=1.0)
			row.operator("object.vertex_group_select", text = "Select")
			row.operator("object.vertex_group_deselect", text = "Deelect")

			column = layout.column()
			split = column.split(factor = 0.91, align = True)

			split.prop(context.scene.tool_settings, 'vertex_group_weight', text = "Weight")
			if context.scene.tool_settings.vertex_group_weight > 0:
				split.operator("object.toggle_0_1_vertex_weight", text = "", icon = 'RADIOBUT_ON').value = 0.0
			else:
				split.operator("object.toggle_0_1_vertex_weight", text = "", icon = 'RADIOBUT_OFF').value = 1.0

			column.operator("object.sync_vg", text = "Sync with Bones", icon='UV_SYNC_SELECT')

class VertexPaintPanel(Panel):
	bl_label = "Vertex Paint"
	bl_idname = "OBJECT_PT_AUT_VERTEX_PAINT_PANEL"
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = "Automation Tools"
	bl_options =  {'DEFAULT_CLOSED'}
	bl_parent_id = ModelingPanel.bl_idname

	@classmethod
	def poll(cls, context):
		return context.object is not None and context.object.type == 'MESH'

	def draw(self, context):
		layout = self.layout
		column = layout.column(align=True)				
		box = layout.box()
		row = box.row()
		column = row.column(align=True)
		row.prop(context.object.data, 'use_paint_mask', text='')
		row.operator(FillVertexColors.bl_idname, text = "Custom", icon='COLOR')
		row.operator(FillVertexColors.bl_idname, text = "", icon='RGB_RED').color = Vector((1,0,0,1))
		row.operator(FillVertexColors.bl_idname, text = "", icon='RGB_GREEN').color = Vector((0,1,0,1))
		row.operator(FillVertexColors.bl_idname, text = "", icon='RGB_BLUE').color = Vector((0,0,1,1))
		row.operator(FillVertexColors.bl_idname, text = "", icon='EVENT_W').color = Vector((1,1,1,1))
		row.operator(FillVertexColors.bl_idname, text = "", icon='EVENT_B').color = Vector((0,0,0,1))
		
		# row = row.column(align=True)
		# column.operator(ChangeVertexColorBrightness.bl_idname, text="Brightness")		
		column = layout.column()			
		# column.operator(InvertVertexColors.bl_idname, text="Invert")
		column.operator(ConvertAOtoExhaustHeatMap.bl_idname, text="AO to Exhaust Glow", icon='GP_MULTIFRAME_EDITING')
		column.operator(ChangeVertexColorBrightness.bl_idname, text="Brightness", icon='MOD_BRIGHTNESS_CONTRAST')	

class BrushPanel(Panel):
	bl_label = "Brush"
	bl_idname = "OBJECT_PT_AUT_RIG_SK_BRUSH_PANEL"
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = "Automation Tools"
	bl_options =  {'DEFAULT_CLOSED'}
	bl_parent_id = RiggingSkinningPanel.bl_idname

	def draw(self, context):
		layout = self.layout

class BrushAddSubPanel(Panel):
	bl_label = "Add/Sub"
	bl_idname = "OBJECT_PT_AUT_RIG_SK_BRUSH_ADD_SUB_PANEL"
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = "Automation Tools"
	bl_options =  {'DEFAULT_CLOSED'}
	bl_parent_id = BrushPanel.bl_idname

	def draw(self, context):
		layout = self.layout
		column = layout.column(align=True)

		split = column.split(factor=0.5, align=True)
		if bpy.data.brushes["Draw"].blend == 'ADD':
			split.operator("brush.draw_brush_blend_toggle", text = "Add", depress = True).mode='ADD'
		else:
			split.operator("brush.draw_brush_blend_toggle", text = "Add", depress = False).mode='ADD'

		if bpy.data.brushes["Draw"].blend == 'SUB':
			split.operator("brush.draw_brush_blend_toggle", text = "Sub", depress = True).mode ='SUB'
		else:
			split.operator("brush.draw_brush_blend_toggle", text = "Sub", depress = False).mode ='SUB'

		column.operator("brush.toggle_draw_brush_add_sub", text = "Add / Sub")

class BrushCustomizedSettingsPanel(Panel):
	bl_label = "Presets"
	bl_idname = "OBJECT_PT_AUT_RIG_SK_BRUSH_CUSTOMIZED_PANEL"
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = "Automation Tools"
	bl_options =  {'DEFAULT_CLOSED'}
	bl_parent_id = BrushPanel.bl_idname

	def draw(self, context):
		layout = self.layout
		column = layout.column()

		column.operator("brush.draw_brush_template_settings_1", text = "Preset 1")
		column.operator("brush.draw_brush_template_settings_2", text = "Preset 2")

class WeightsPanel(Panel):
	bl_label = "Weights"
	bl_idname = "OBJECT_PT_AUT_RIG_SK_WEIGHTS_PANEL"
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = "Automation Tools"
	bl_options =  {'DEFAULT_CLOSED'}
	bl_parent_id = RiggingSkinningPanel.bl_idname

	def draw(self, context):
		layout = self.layout

		column = layout.column(align=True)
		weight_bar = column.split(factor=0.7, align=True)
		weight_bar.prop(bpy.context.scene, 'vertex_weight_input')

		weight_bar.operator("view3d.tenfold_weight", text = "x2").value = 2
		weight_bar.operator("view3d.tenfold_weight", text = "x10").value = 10
		weight_bar.operator("view3d.tenfold_weight", text = "/10").value = 0.1
		weight_bar.operator("view3d.tenfold_weight", text = "/2").value = 0.5


		column = layout.column(align=True)
		split1 = column.split(factor=0.33, align=True)

		add = split1.operator("object.fill_active_vg", text = "Add")
		add.mode = 'ADD'
		add.multiplier = 0

		mlt = split1.operator("object.fill_active_vg", text = "x2")
		mlt.mode = 'ADD'
		mlt.multiplier = 2

		neg_mlt = split1.operator("object.fill_active_vg", text = "/2")
		neg_mlt.mode = 'SUBTRACT'
		neg_mlt.multiplier = 2

		split1.operator("object.fill_active_vg", text = "Subtract").mode = 'SUBTRACT'

		column = layout.column()
		column.operator("object.clamp_near_zero_values", text = "Clamp")
		column.operator("object.fill_active_vg", text = "Replace").mode = 'REPLACE'

class NormalsPanel(Panel):
	bl_label = "Normals"
	bl_idname = "OBJECT_PT_AUT_NORMALS_PANEL"
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = "Automation Tools"
	bl_options =  {'DEFAULT_CLOSED'}
	bl_parent_id = GeometryPanel.bl_idname

	def draw(self, context):
		layout = self.layout
		column = layout.column(align=True)

		column.operator("mesh.customdata_custom_splitnormals_clear", text = "Split")
		column.operator("object.reset_normals_object", text = "Reset")

class TransformPanel(Panel):
	bl_label = "Transform"
	bl_idname = "OBJECT_PT_TRANSFORM_PANEL"
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = "Automation Tools"
	bl_options =  {'DEFAULT_CLOSED'}
	bl_parent_id = GeometryPanel.bl_idname

	def draw(self, context):
		layout = self.layout
		column = layout.column(align=True)

		
		column.label(text = "Cursor:")
		column.operator(AT_SnapCursorToSelectedVerts.bl_idname, text = "Snap To Verts")
		column.operator(AT_CursorToZero.bl_idname, text = "Snap to XYZ")
		column.separator()

		column.label(text = "Curve:")
		column.operator(AT_SnapCurveToTarget.bl_idname, text = "Snap Curve To Target")
		column.operator(AT_SnapBezierPointToCursor.bl_idname, text = "Snap Bezier Point To Cursor")			
		
		column.label(text = "Mesh:")
		column.operator("object.transfer_transform", text = "Transfer")
		column.operator(AT_ResetTransform.bl_idname, text = "Reset")
		column.operator(AT_SetMeshPositionToZero.bl_idname, text = "Snap to XYZ")
		column.operator("object.move_to_scene_center", text = "Move to Scene Origin")
		column.separator()		
		row = column.row(align=True)
		row.operator(AT_SnapRotateMeshToTarget.bl_idname, text = "Dial Mesh")
		row.operator(AT_SnapRotateVertsToTarget.bl_idname, text = "Dial Verts")		
		column.separator()
		column.operator("object.duplicate_offset", text = "Duplicate Linear")
		column.operator("object.duplicate_circular", text = "Duplicate Circular")
		column.separator()

		# column.label(text = "Random Rotation:")
		# row = column.row(align=True)
		# row.operator("object.rotate_random", text = "X").axis = 0
		# row.operator("object.rotate_random", text = "Y").axis = 1
		# row.operator("object.rotate_random", text = "Z").axis = 2
		# column.separator()		

		column.separator()		
		column.label(text = "Get UE Transform:")
		row = column.row(align=True)
		row.operator(GetUETransform.bl_idname, text = "Translation").type='TRANSLATION'
		row.operator(GetUETransform.bl_idname, text = "Rotation").type='ROTATION'
		row.operator(GetUETransform.bl_idname, text = "Scale").type='SCALE'
		
		column.separator()
		column = layout.column(align=False)
		column.operator(GetUEBoneConstraints.bl_idname, text = "Get UE Bone Limits")
		
		column.label(text = "Get UE Transforms:")
		row = column.row(align=True)
		row.operator(GetUETransforms.bl_idname, text = "Objects")
		row.operator(GetUESplinePoints.bl_idname, text = "Curve")
		row.operator(GetCamsoSplinePoints.bl_idname, text = "Curves")
		row = column.row(align=True)
		row.prop(bpy.context.scene, "copy_transform_offset")		

		column.separator()		
		column.label(text = "Set UE Transform:")
		row = column.row(align=True)
		row.operator(SetUETransform.bl_idname, text = "Translation").type='TRANSLATION'
		row.operator(SetUETransform.bl_idname, text = "Rotation").type='ROTATION'
		row.operator(SetUETransform.bl_idname, text = "Scale").type='SCALE'

class ModesPanel(Panel):
	bl_label = "Modes"
	bl_idname = "OBJECT_PT_AUT_RIG_SK_MODES_PANEL"
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = "Automation Tools"
	bl_options =  {'DEFAULT_CLOSED'}

	def draw(self, context):
		layout = self.layout
		column = layout.column(align=True)

		split = column.split(factor=0.5, align=True)
		split.operator("object.object_edit_mode_on", text = "Object", icon='OBJECT_DATA').mode='OBJECT'
		split.operator("object.object_edit_mode_on", text = "Edit", icon='EDITMODE_HLT').mode='EDIT'
		column.operator("object.weight_paint_mode_on", icon='MOD_VERTEX_WEIGHT', text = "Weight")
		column.operator("object.pose_mode_on", icon='POSE_HLT', text = "Pose")
		column.operator("object.toggle_weight_pose_modes", text = "Weight / Pose", icon='ARROW_LEFTRIGHT')

class ShadingPanel(Panel):
	bl_label = "Shading"
	bl_idname = "OBJECT_PT_AUT_RIG_SK_SHADING_PANEL"
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = "Automation Tools"
	bl_options =  {'DEFAULT_CLOSED'}
	bl_parent_id = ModelingPanel.bl_idname

	def draw(self, context):
		layout = self.layout
		column = layout.column()
		column.operator("view3d.toggle_carpaint", text = "Car Paint / Basic")
		column.operator('object.at_assign_color', text = "Assign Color")		

class TriangulationPanel(Panel):
	bl_label = "Triangulation"
	bl_idname = "OBJECT_PT_AUT_TRIANGULATION_PANEL"
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = "Automation Tools"
	bl_options =  {'DEFAULT_CLOSED'}
	bl_parent_id = GeometryPanel.bl_idname

	def draw(self, context):
		layout = self.layout
		column = layout.column(align=True)
		column.operator("mesh.rotate_edge_triangulation_quads", text = 'Rotate Edges Beauty').quad_method = 'BEAUTY'
		column.operator("mesh.rotate_edge_triangulation_quads", text = 'Rotate Edges Fixed').quad_method = 'FIXED_ALTERNATE'
		column.separator()
		column.operator("OBJECT_OT_at_wiki", text = "Help", icon = "HELP").tool = 'fix_triangulation'

# class SceneUtilsPanel(Panel):
# 	bl_label = "Scene Utils"
# 	bl_idname = "OBJECT_PT_AUT_SCENE_UTILS_PANEL"
# 	bl_space_type = 'VIEW_3D'
# 	bl_region_type = 'UI'
# 	bl_category = "Automation Tools"
# 	bl_options =  {'DEFAULT_CLOSED'}
# 	bl_parent_id = UtilsPanel.bl_idname

# 	def draw(self, context):
# 		layout = self.layout
# 		column = layout.column(align=True)

class ModifiersPanel(Panel):
	bl_label = "Modifiers"
	bl_idname = "OBJECT_PT_AUT_RIG_SK_MODIFIERS_PANEL"
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = "Automation Tools"
	bl_options =  {'DEFAULT_CLOSED'}
	bl_parent_id = ModelingPanel.bl_idname

	def draw(self, context):
		layout = self.layout
		column = layout.column(align=True)

		column.operator("view3d.toggle_all_modifiers_visibility", text = "Toggle All")
		column.operator("object.transfer_modifiers", text = "Transfer")
		column.operator("view3d.copy_apply_modifier", text = "Copy and Apply")
		column.operator("object.apply_modifiers_with_shape_keys", text = 'Apply [with Shape Keys]')
		column.separator()
		column.operator("OBJECT_OT_at_wiki", text = "Help", icon = "HELP").tool = 'modifiers'

class StandardBatchExportPanel(Panel):
	bl_label = "Batch"
	bl_idname = "OBJECT_PT_Standard_Batch_Export_Panel"
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = "Automation Tools"
	bl_options =  {'DEFAULT_CLOSED'}
	bl_parent_id = ExportPanel.bl_idname

	def draw(self, context):
		layout = self.layout
		column = layout.column(align=True)
		column.operator("object.standard_batch_export", text = "Export")

class BodyExportPanel(Panel):
	bl_label = "Body"
	bl_idname = "OBJECT_PT_AUTOMATION_TOOLS_BODY_EXPORT_PANEL"
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = "Automation Tools"
	bl_options =  {'DEFAULT_CLOSED'}
	bl_parent_id = ExportPanel.bl_idname

	def draw(self, context):
		layout = self.layout
		column = layout.column(align=True)
		column.operator(BodyExport.bl_idname, text = "One Collection")
		column.operator(BodiesBatchExport.bl_idname, text = "All Collections")
		column.prop(bpy.context.scene, "if_apply_modifiers")
		column.prop(bpy.context.scene, "debug_mode")

class RimExportPanel(Panel):
	bl_label = "Rim"
	bl_idname = "OBJECT_PT_AUTOMATION_TOOLS_RIM_EXPORT_PANEL"
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = "Automation Tools"
	bl_options =  {'DEFAULT_CLOSED'}
	bl_parent_id = ExportPanel.bl_idname


	def draw(self, context):
		layout = self.layout
		column = layout.column(align=True)
		column.operator("object.rim_export", text = "One Collection")
		column.operator("object.rim_batch_export", text = "All Collections")
		column.prop(bpy.context.scene, "debug_mode")

class HierarchyExportPanel(Panel):
	bl_label = "Hierarchy"
	bl_idname = "OBJECT_PT_AUTOMATION_TOOLS_EXPORT_PANEL_2"
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = "Automation Tools"
	bl_options =  {'DEFAULT_CLOSED'}
	bl_parent_id = ExportPanel.bl_idname

	def draw(self, context):
		layout = self.layout
		column = layout.column(align=True)		
		column.operator("object.fast_auto_fbx_export", text = "Export")
		column.prop(bpy.context.scene, "if_lods")
		column.prop(bpy.context.scene, "zeroout_location_and_rotation")
		column.prop(bpy.context.scene, "join_root_elements")

class ModularExportPanel(Panel):
	bl_label = "Modular"
	bl_idname = "OBJECT_PT_AUTOMATION_TOOLS_EXPORT_MODULAR"
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = "Automation Tools"
	bl_options =  {'DEFAULT_CLOSED'}
	bl_parent_id = ExportPanel.bl_idname
	
	def draw(self, context):
		layout = self.layout
		column = layout.column(align=True)
		column.prop(bpy.context.scene, "at_modular_mesh_name", text='', placeholder='Base Name')
		column.separator()
		
		row = column.row(align=True)
		row.label(text='Limits type:')
		row.prop(context.scene, "at_modular_limits_type", text='')		
		limits_type = context.scene.at_modular_limits_type		
		column.separator()	
		match (limits_type):
			case 'X-Coords':							
				row = column.row(align=True)
				row.prop(context.scene, "at_modular_numeric_limits")
				row.separator()
				row.operator('object.at_export_modular_mesh', text="Set").mode='SET_LIMITS'
			case 'Color':
				obj = context.object
				if obj is not None and obj.type == 'MESH':				
					mesh = obj.data			
					row = layout.row()
					column = row.column()
					column.template_list(
						"MESH_UL_color_attributes",
						"color_attributes",
						mesh,
						"color_attributes",
						mesh.color_attributes,
						"active_color_index",
						rows=3,
					)

					column = row.column(align=True)
					column.operator("geometry.color_attribute_add", icon='ADD', text="")
					column.operator("geometry.color_attribute_remove", icon='REMOVE', text="")
					column.separator()
					column.menu("MESH_MT_color_attribute_context_menu", icon='DOWNARROW_HLT', text="")

		column = layout.column(align=True)	
		column.separator()
		column.operator('object.at_export_modular_mesh', text="Debug").mode='DEBUG'
		column.operator('object.at_export_modular_mesh', text="Export").mode='EXPORT'

class FixturesExportPanel(Panel):
	bl_label = "Fixtures"
	bl_idname = "OBJECT_PT_AUTOMATION_TOOLS_EXPORT_PANEL_3"
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = "Automation Tools"
	bl_options =  {'DEFAULT_CLOSED'}
	bl_parent_id = ExportPanel.bl_idname

	def draw(self, context):
		layout = self.layout
		column = layout.column(align=True)

		column.operator("object.selected_fixtures_batch_export", text = "Selected Meshes")
		column.operator("object.fixture_export", text = "Active Collection")
		column.operator("object.fixtures_batch_export", text = "Batch Collections")

class OptionsPanel(Panel):
	bl_label = "Options"
	bl_idname = "OBJECT_PT_AUT_RIG_SK_OPTIONS_PANEL"
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = "Automation Tools"
	bl_options =  {'DEFAULT_CLOSED'}
	bl_parent_id = RiggingSkinningPanel.bl_idname

	def draw(self, context):
		layout = self.layout
		column = layout.column(align=True)

		column.label(text = 'Vertex Groups:')
		column.prop(bpy.context.scene, 'select_all_vg_vertices')
		column.prop(bpy.context.scene, 'lock_all_unused_vgs')
		column.prop(bpy.context.scene, 'auto_add_vertex_group')


# Menus
class GenerateRigMenu(Menu):
	bl_label = "Add Bone"
	bl_idname = "OBJECT_MT_generate_rig_menu"
	bl_description = "Add Car Body Bones"

	def draw(self, context):
		layout = self.layout

		layout.operator("object.generate_rig", text = "New Bone").name= 'New_Bone'

		layout.menu("OBJECT_MT_fender_sub_menu", text = "Fender")
		layout.menu("OBJECT_MT_quarter_sub_menu", text = "Quarter")
		layout.menu("OBJECT_MT_side_sub_menu", text = "Side")
		layout.menu("OBJECT_MT_rocker_sub_menu", text = "Rocker")

		cabin_wigth = layout.operator("object.generate_rig", text = "Cabin Width")
		cabin_wigth.name= 'R_CabinWidth'

		layout.menu("OBJECT_MT_front_sub_menu", text = "Front")
		layout.menu("OBJECT_MT_rear_sub_menu", text = "Rear")
		layout.menu("OBJECT_MT_pillar_sub_menu", text = "Pillar")
		layout.menu("OBJECT_MT_roof_sub_menu", text = "Roof")
		layout.menu("OBJECT_MT_cargo_sub_menu", text = "Cargo")
		layout.menu("OBJECT_MT_hood_sub_menu", text = "Hood")
		layout.menu("OBJECT_MT_boot_sub_menu", text = "Boot")
		layout.menu("OBJECT_MT_front_side_sub_menu", text = "Front Side")
		layout.menu("OBJECT_MT_rear_side_sub_menu", text = "Rear Side")
		layout.menu("OBJECT_MT_front_bumper_sub_menu", text = "Front Bumper")
		layout.menu("OBJECT_MT_rear_bumper_sub_menu", text = "Rear_Bumper")

		bed_hight = layout.operator("object.generate_rig", text = "Bed Height")
		bed_hight.name= 'Bed_Height'

		layout.menu("OBJECT_MT_wheel_well_sub_menu", text = "Wheel Well")

class FenderSubMenu(Menu):
	bl_label = "Fender Menu"
	bl_idname = "OBJECT_MT_fender_sub_menu"

	def draw(self, context):
		layout = self.layout

		bone1 = layout.operator("object.generate_rig", text = "Fender")
		bone1.name='R_Fender'
		

		bone2 = layout.operator("object.generate_rig", text = "Lip")
		bone2.name='R_FenderLip'
		

		bone3 = layout.operator("object.generate_rig", text = "Height")
		bone3.name='R_FenderHeight'
		

		bone4 = layout.operator("object.generate_rig", text = "Arch Size")
		bone4.name='Fender_Arch_Size'



class QuarterSubMenu(Menu):
	bl_label = "Quarter Menu"
	bl_idname = "OBJECT_MT_quarter_sub_menu"

	def draw(self, context):
		layout = self.layout

		bone1 = layout.operator("object.generate_rig", text = "Quarter")
		bone1.name='R_Quarter'
		

		bone2 = layout.operator("object.generate_rig", text = "Lip")
		bone2.name='R_QuarterLip'
		

		bone3 = layout.operator("object.generate_rig", text = "Height")
		bone3.name='R_QuarterHeight'
		

		bone4 = layout.operator("object.generate_rig", text = "Arch Size")
		bone4.name='Quarter_Arch_Size'


class SideSubMenu(Menu):
	bl_label = "Side Menu"
	bl_idname = "OBJECT_MT_side_sub_menu"

	def draw(self, context):
		layout = self.layout

		bone1 = layout.operator("object.generate_rig", text = "Side")
		bone1.name='R_Side'
		

		bone2 = layout.operator("object.generate_rig", text = "Detail 1")
		bone2.name='R_SideDetail1'
		

		bone3 = layout.operator("object.generate_rig", text = "Detail 2")
		bone3.name='R_SideDetail2'
		

		bone4 = layout.operator("object.generate_rig", text = "Detail 3")
		bone4.name='R_SideDetail3'


class RockerSubMenu(Menu):
	bl_label = "Rocker Menu"
	bl_idname = "OBJECT_MT_rocker_sub_menu"

	def draw(self, context):
		layout = self.layout

		bone1 = layout.operator("object.generate_rig", text = "Panel")
		bone1.name='R_RockerPanel'
		

		bone2 = layout.operator("object.generate_rig", text = "Detail")
		bone2.name='R_RockerDetail'
		

class FrontSubMenu(Menu):
	bl_label = "Front Menu"
	bl_idname = "OBJECT_MT_front_sub_menu"

	def draw(self, context):
		layout = self.layout

		bone1 = layout.operator("object.generate_rig", text = "Length")
		bone1.name='Front_Length'
		

		bone2 = layout.operator("object.generate_rig", text = "Angle")
		bone2.name='R_FrontAngle'
		

		bone3 = layout.operator("object.generate_rig", text = "Detail 1")
		bone3.name='Front_Detail_1'


		bone4 = layout.operator("object.generate_rig", text = "Detail 2")
		bone4.name='Front_Detail_2'


		bone5 = layout.operator("object.generate_rig", text = "Detail 3")
		bone5.name='Front_Detail_3'


class RearSubMenu(Menu):
	bl_label = "Rear Menu"
	bl_idname = "OBJECT_MT_rear_sub_menu"

	def draw(self, context):
		layout = self.layout

		bone1 = layout.operator("object.generate_rig", text = "Length")
		bone1.name='Rear_Length'
		

		bone2 = layout.operator("object.generate_rig", text = "Angle")
		bone2.name='R_RearAngle'
		

		bone3 = layout.operator("object.generate_rig", text = "Detail 1")
		bone3.name='Rear_Detail_1'


		bone4 = layout.operator("object.generate_rig", text = "Detail 2")
		bone4.name='Rear_Detail_2'


		bone5 = layout.operator("object.generate_rig", text = "Detail 3")
		bone5.name='Rear_Detail_3'



class PillarSubMenu(Menu):
	bl_label = "Pillar Menu"
	bl_idname = "OBJECT_MT_pillar_sub_menu"

	def draw(self, context):
		layout = self.layout

		bone1 = layout.operator("object.generate_rig", text = "A Pillar")
		bone1.name='A_Pillar'
		

		bone2 = layout.operator("object.generate_rig", text = "A Adjustment")
		bone2.name='A_Pillar_Adjustment'


		bone3 = layout.operator("object.generate_rig", text = "A Upper")
		bone3.name='A_Pillar_Upper'


		bone4 = layout.operator("object.generate_rig", text = "A Mid")
		bone4.name='A_Pillar_Mid'


		bone5 = layout.operator("object.generate_rig", text = "A Lower")
		bone5.name='A_Pillar_Lower'


		bone6 = layout.operator("object.generate_rig", text = "B Pillar")
		bone6.name='B_Pillar'


		bone7 = layout.operator("object.generate_rig", text = "B Adjustment")
		bone7.name='B_Pillar_Adjustment'


		bone8 = layout.operator("object.generate_rig", text = "B Upper")
		bone8.name='B_Pillar_Upper'


		bone9 = layout.operator("object.generate_rig", text = "B Mid")
		bone9.name='B_Pillar_Mid'


		bone10 = layout.operator("object.generate_rig", text = "B Lower")
		bone10.name='B_Pillar_Lower'


		bone11 = layout.operator("object.generate_rig", text = "C Pillar")
		bone11.name='C_Pillar'


		bone12 = layout.operator("object.generate_rig", text = "C Adjustment")
		bone12.name='C_Pillar_Adjustment'


		bone13 = layout.operator("object.generate_rig", text = "C Upper")
		bone13.name='C_Pillar_Upper'


		bone14 = layout.operator("object.generate_rig", text = "C Mid")
		bone14.name='C_Pillar_Mid'


		bone15 = layout.operator("object.generate_rig", text = "C Lower")
		bone15.name='C_Pillar_Lower'


		bone16 = layout.operator("object.generate_rig", text = "D Pillar")
		bone16.name='D_Pillar'


		bone17 = layout.operator("object.generate_rig", text = "D Adjustment")
		bone17.name='D_Pillar_Adjustment'


		bone18 = layout.operator("object.generate_rig", text = "D Upper")
		bone18.name='D_Pillar_Upper'


		bone19 = layout.operator("object.generate_rig", text = "D Mid")
		bone19.name='D_Pillar_Mid'


		bone20 = layout.operator("object.generate_rig", text = "D Lower")
		bone20.name='D_Pillar_Lower'


class RoofSubMenu(Menu):
	bl_label = "Roof Menu"
	bl_idname = "OBJECT_MT_roof_sub_menu"

	def draw(self, context):
		layout = self.layout

		bone1 = layout.operator("object.generate_rig", text = "Height")
		bone1.name='Roof_Height'
		

		bone2 = layout.operator("object.generate_rig", text = "Detail")
		bone2.name='Roof_Detail'


class CargoSubMenu(Menu):
	bl_label = "Roof Menu"
	bl_idname = "OBJECT_MT_cargo_sub_menu"

	def draw(self, context):
		layout = self.layout

		bone1 = layout.operator("object.generate_rig", text = "Height")
		bone1.name='Cargo_Height'
		

		bone2 = layout.operator("object.generate_rig", text = "Detail")
		bone2.name='Cargo_Detail'


class HoodSubMenu(Menu):
	bl_label = "Hood Menu"
	bl_idname = "OBJECT_MT_hood_sub_menu"

	def draw(self, context):
		layout = self.layout

		bone1 = layout.operator("object.generate_rig", text = "Angle")
		bone1.name='R_HoodAngle'
		

		bone2 = layout.operator("object.generate_rig", text = "Slant")
		bone2.name='Hood_Slant'
		

		bone3 = layout.operator("object.generate_rig", text = "Detail 1")
		bone3.name='Hood_Detail_1'


		bone4 = layout.operator("object.generate_rig", text = "Detail 2")
		bone4.name='Hood_Detail_2'


		bone5 = layout.operator("object.generate_rig", text = "Detail 3")
		bone5.name='Hood_Detail_3'


class BootSubMenu(Menu):
	bl_label = "Boot Menu"
	bl_idname = "OBJECT_MT_boot_sub_menu"

	def draw(self, context):
		layout = self.layout

		bone1 = layout.operator("object.generate_rig", text = "Angle")
		bone1.name='R_BootAngle'
		

		bone2 = layout.operator("object.generate_rig", text = "Slant")
		bone2.name='Boot_Slant'


		bone3 = layout.operator("object.generate_rig", text = "Detail 1")
		bone3.name='Boot_Detail_1'


		bone4 = layout.operator("object.generate_rig", text = "Detail 2")
		bone4.name='Boot_Detail_2'


		bone5 = layout.operator("object.generate_rig", text = "Detail 3")
		bone5.name='Boot_Detail_3'


class FrontBumperSubMenu(Menu):
	bl_label = "Front Bumper Menu"
	bl_idname = "OBJECT_MT_front_bumper_sub_menu"

	def draw(self, context):
		layout = self.layout

		bone1 = layout.operator("object.generate_rig", text = "Front")
		bone1.name='Front_Bumper'
		

		bone2 = layout.operator("object.generate_rig", text = "Lip")
		bone2.name='Front_Bumper_Lip'


		bone3 = layout.operator("object.generate_rig", text = "Upper")
		bone3.name='Front_Bumper_Upper'


		bone4 = layout.operator("object.generate_rig", text = "Lower")
		bone4.name='Front_Bumper_Lower'


		bone5 = layout.operator("object.generate_rig", text = "Detail 1")
		bone5.name='Front_Bumper_Detail_1'


		bone6 = layout.operator("object.generate_rig", text = "Detail 2")
		bone6.name='Front_Bumper_Detail_2'


		bone7 = layout.operator("object.generate_rig", text = "Detail 3")
		bone7.name='Front_Bumper_Detail_3'


class RearBumperSubMenu(Menu):
	bl_label = "Rear Bumper Menu"
	bl_idname = "OBJECT_MT_rear_bumper_sub_menu"

	def draw(self, context):
		layout = self.layout

		bone1 = layout.operator("object.generate_rig", text = "Rear")
		bone1.name='Rear_Bumper'
		

		bone2 = layout.operator("object.generate_rig", text = "Lip")
		bone2.name='Rear_Bumper_Lip'


		bone3 = layout.operator("object.generate_rig", text = "Upper")
		bone3.name='Rear_Bumper_Upper'


		bone4 = layout.operator("object.generate_rig", text = "Lower")
		bone4.name='Rear_Bumper_Lower'


		bone5 = layout.operator("object.generate_rig", text = "Detail 1")
		bone5.name='RearBumper_Detail_1'


		bone6 = layout.operator("object.generate_rig", text = "Detail 2")
		bone6.name='Rear_Bumper_Detail_2'


		bone7 = layout.operator("object.generate_rig", text = "Detail 3")
		bone7.name='Rear_Bumper_Detail_3'


class FrontSideSubMenu(Menu):
	bl_label = "Front Side Menu"
	bl_idname = "OBJECT_MT_front_side_sub_menu"

	def draw(self, context):
		layout = self.layout

		bone1 = layout.operator("object.generate_rig", text = "Front Side 1")
		bone1.name='R_FrontSide1'
		

		bone2 = layout.operator("object.generate_rig", text = "Front Side 2")
		bone2.name='R_FrontSide2'
		

class RearSideSubMenu(Menu):
	bl_label = "Rear Side Menu"
	bl_idname = "OBJECT_MT_rear_side_sub_menu"

	def draw(self, context):
		layout = self.layout

		bone1 = layout.operator("object.generate_rig", text = "Rear Side 1")
		bone1.name='R_RearSide1'
		

		bone2 = layout.operator("object.generate_rig", text = "Rear Side 2")
		bone2.name='R_RearSide2'
		

class WheelWellSubMenu(Menu):
	bl_label = "Rear Side Menu"
	bl_idname = "OBJECT_MT_wheel_well_sub_menu"

	def draw(self, context):
		layout = self.layout

		bone1 = layout.operator("object.generate_rig", text = "Width")
		bone1.name='R_Wheel_Well_Width'
		

		bone2 = layout.operator("object.generate_rig", text = "Position")
		bone2.name='Wheel_Well_Position'


class SelectBonesMenu(Menu):
	bl_idname = "OBJECT_MT_select_bones_menu"
	bl_label = "Select Bones"
	bl_description = "Select bones menu"

	def draw(self, context):
		if context.object is not None:
			if get_bones(self) is not None:
				layout = self.layout
				bones = get_bones(self)

				if len(bones) > 1:
					for i in bones:
						layout.operator("armature.select_bones_and_mode", text = i.name).name= i.name

class PIE_MT_RigSk_tools(Menu):
	bl_label = "Brushes"

	def draw(self, context):
		layout = self.layout
		pie = layout.menu_pie()
		pie.operator("brush.draw_brush_blend_toggle", text = "Add").mode='ADD'
		pie.operator("brush.draw_brush_blend_toggle", text = "Sub").mode ='SUB'
		pie.operator("wm.tool_set_by_id", text = "Average").name="builtin_brush.Average"
		pie.operator("wm.tool_set_by_id", text = "Blur").name="builtin_brush.Blur"

class PIE_MT_RigSk_tools_modes(Menu):
	bl_label = "Modes"

	def draw(self, context):
		layout = self.layout
		pie = layout.menu_pie()
		pie.operator("object.weight_paint_mode_on", text = "Weight Paint")
		pie.operator("object.pose_mode_on", text = "Pose")
		pie.operator("object.object_edit_mode_on", text = "Edit").mode='EDIT'
		pie.operator("object.object_edit_mode_on", text = "Object").mode='OBJECT'

class RigSkToolsPMDraw(Operator):
	bl_label = 'Rigging/Skinning Brushes Pie Menu'
	bl_idname = "paint.pie_menu_rig_sk"

	def execute(self, context):
		bpy.ops.wm.call_menu_pie(name="PIE_MT_RigSk_tools")
		return {'FINISHED'}

class RigSkToolsPMModes(Operator):
	bl_label = 'Rigging/Skinning Modes Pie Menu'
	bl_idname = "view3d.pie_menu_rig_sk_modes"

	def execute(self, context):
		bpy.ops.wm.call_menu_pie(name="PIE_MT_RigSk_tools_modes")
		return {'FINISHED'}

#Wiki
class ATWiki(Operator):
	bl_idname = "object.at_wiki"
	bl_label = "Automation Tools Documentation"
	bl_description = "Automation Tools Wiki on GitHub"
	tool: bpy.props.StringProperty(options = {'HIDDEN'})

	def execute(self, context):
		links_map = {
		"rim_generator" : 'https://github.com/AutomationStaff/AutomationTools/wiki/Generators#rim-generator-tool',
		"active_mesh": 'https://github.com/AutomationStaff/AutomationTools/wiki/Active-Mesh',
		'uvs_lights': 'https://github.com/AutomationStaff/AutomationTools/wiki/Modeling#lights',
		'fix_triangulation': 'https://github.com/AutomationStaff/AutomationTools/wiki/Modeling#triangulation',
		'modifiers': 'https://github.com/AutomationStaff/AutomationTools/wiki/Modeling#modifiers'
		}

		url = links_map[self.tool]
		webbrowser.open_new(url)
		return {'FINISHED'}

classes = (
	ActiveMeshPanel,
	ModesPanel,
	ModelingPanel,
	GeneratorsPanel,
	RiggingSkinningPanel,
	# UtilsPanel,
	ExportPanel,
	# SceneUtilsPanel,
	NamesPanel,
	UVsPanel,
	GeometryPanel,
	TransformPanel,
	BonesPanel,
	VertexGroupsPanel,
	WeightsPanel,
	VertexPaintPanel,
	ShapeKeysPanel,
	BrushPanel,
	BrushAddSubPanel,
	BrushCustomizedSettingsPanel,
	NormalsPanel,
	ModifiersPanel,
	TriangulationPanel,
	LightsUVsPanel,
	MaterialsPanel,
	MaterialsAddPanel,
	MaterialsCleanupPanel,
	HierarchyPanel,
	ShadingPanel,
	RimGeneratorPanel,
	BodyExportPanel,
	RimExportPanel,
	HierarchyExportPanel,
	FixturesExportPanel,
	StandardBatchExportPanel,
	OptionsPanel,
	GenerateRigMenu,
	FenderSubMenu,
	QuarterSubMenu,
	SideSubMenu,
	RockerSubMenu,
	FrontSubMenu,
	RearSubMenu,
	PillarSubMenu,
	RoofSubMenu,
	CargoSubMenu,
	HoodSubMenu,
	BootSubMenu,
	FrontBumperSubMenu,
	RearBumperSubMenu,
	FrontSideSubMenu,
	RearSideSubMenu,
	WheelWellSubMenu,
	PIE_MT_RigSk_tools,
	PIE_MT_RigSk_tools_modes,
	RigSkToolsPMModes,
	RigSkToolsPMDraw,
	SelectBonesMenu,
	SocketsPanel,
	UVToolsPanel,
	ATWiki,
	MaterialsEditPanel,
	BodyUVs,
	ModularExportPanel,
	BackupPanel
)

# Functions
def edit_wp_pose_buttons(self, context):
	if context.object:
		layout = self.layout
		column = layout.column(align=True)
		split = column.split(align=True)
		# Edit
		if context.scene.edit_on_off == False:
			edit = split.operator("scene.state_edit_pose_wp_buttons", text = "Edit", depress = False)
			edit.pose_on = False
			edit.wp_on = False
			edit.edit_on = True
		else:
			edit = split.operator("scene.state_edit_pose_wp_buttons", text = "Edit", depress = True)
			edit.pose_on = False
			edit.wp_on = False
			edit.edit_on = False

		# Pose
		if context.scene.pose_on_off == False:
			pos = split.operator("scene.state_edit_pose_wp_buttons", text = "Pose", depress = False)
			pos.pose_on = True
			pos.wp_on = False
			pos.edit_on = False
		else:
			pos = split.operator("scene.state_edit_pose_wp_buttons", text = "Pose", depress = True)
			pos.pose_on = False
			pos.wp_on = False
			pos.edit_on = False

		# Weight Paint
		if context.scene.weight_paint_on_off == False:
			wp = split.operator("scene.state_edit_pose_wp_buttons", text = "Weight", depress = False)
			wp.wp_on = True
			wp.pose_on = False
			wp.edit_on = False
		else:
			wp = split.operator("scene.state_edit_pose_wp_buttons", text = "Weight", depress = True)
			wp.wp_on = False
			wp.pose_on = False
			wp.edit_on = False

def register():
	for cls in classes:
		bpy.utils.register_class(cls)

def unregister():
	for cls in reversed(classes):
		bpy.utils.unregister_class(cls)





