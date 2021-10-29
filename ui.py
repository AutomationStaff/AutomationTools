
import bpy
from bpy.utils import register_class, unregister_class
from bpy.types import Panel, Menu, Operator

from . modeling import *
from . generators import *
from . rigging_skinning import *
from . export import *

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
		column.prop(bpy.context.scene, "export_path")

class GeneratorsPanel(Panel):
	bl_label = "Generators"
	bl_idname = "OBJECT_PT_AUTOMATION_TOOLS_GENERATORS_PANEL"
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'	
	bl_category = "Automation Tools"
	bl_options =  {'DEFAULT_CLOSED'}
	
	def draw(self, context):
		layout = self.layout

class RiggingSkinningPanel(Panel):
	bl_label = "Rigging/Skinning"
	bl_idname = "OBJECT_PT_AUT_RIGGING_SKINNING_PANEL"
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'	
	bl_category = "Automation Tools"
	bl_options =  {'DEFAULT_CLOSED'}
	
	def draw(self, context):
		layout = self.layout

# Panels
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
		column.operator("object.add_armature_mod", text = "Add [Armature] [Modifier]")
		column.operator(SelectActiveMesh.bl_idname, text = "Select").mode='EDIT'

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
		column = layout.column(align=True)
		column.operator("object.add_body_materials", text = "Body Mats")
		column.operator("object.add_fixture_materials", text = "Fixture Mats")

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
		column = layout.column(align=False)
		column.operator("OBJECT_OT_rim_generator", text = "New Rim Project")
		column.operator("OBJECT_OT_rim_generator_add_mesh", text = "Add Mesh to Rim Project")

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
		column.operator("object.cleanup_unused_mesh_mats", text = "Mesh Unused")
		column.operator("object.delete_all_mesh_mats", text = "Mesh All")		
		column.operator("object.cleanup_mats_scene_unused", text = "Scene Unused")
		column.operator("object.cleanup_mats_scene_all", text = "Scene All")
		column.operator("object.sort_mesh_materials", text = "Sort")

class NamingPanel(Panel):
	bl_label = "Naming"
	bl_idname = "OBJECT_PT_automation_tools_naming_panel"
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'	
	bl_category = "Automation Tools"
	bl_options =  {'DEFAULT_CLOSED'}
	bl_parent_id = ModelingPanel.bl_idname
	
	def draw(self, context):
		layout = self.layout
		column = layout.column(align=True)

		column.operator("object.object_fix_name", text = "Fix Object Names")
		column.operator("object.fix_material_name", text = "Fix Material Names").symbol = "."

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

		column.operator("OBJECT_OT_generate_hierarchy", text = "Body").type = 'Body'
		column.operator("OBJECT_OT_generate_hierarchy", text = "Rim").type = 'Rim'
		column.operator("OBJECT_OT_generate_hierarchy", text = "Fixture").type = 'Fixture'

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
		
		column.operator("wm.call_menu", text = "Add", icon='ADD').name = GenerateRigMenu.bl_idname
		split = column.split(factor=0.75, align=True)
		split.prop(bpy.context.scene, 'bone_length', slider = True)
		split.operator("object.scale_all_bones", text = "Apply")		
		column.operator("armature.symmetrize", text = "Symmetrize [-X]").direction='NEGATIVE_X'
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

		split = layout.split(factor = 0.91)
		column_left = split.column()
		column_left.template_list(
			listtype_name = "UI_UL_list",
			list_id = 'OBJECT_PT_VG_PANEL',
			dataptr = context.object,
			propname = 'vertex_groups',
			active_dataptr = context.object.vertex_groups,
			active_propname = 'active_index',
			item_dyntip_propname = "Vertex Groups"
		)
		column_right = split.column(align=True)
		column_right.operator("object.vertex_group_add", text = "", icon = 'ADD')
		column_right.operator("object.vertex_group_remove", text = "", icon = 'REMOVE')
		column_right.separator(factor=1.0)
		column_right.operator("wm.call_menu", text = "", icon = 'DOWNARROW_HLT').name = "MESH_MT_vertex_group_context_menu"
		column_right.separator(factor=1.0)
		column_right.operator("object.vertex_group_move", text = "", icon = 'TRIA_UP').direction = 'UP'
		column_right.operator("object.vertex_group_move", text = "", icon = 'TRIA_DOWN').direction = 'DOWN'

		if  len(obj.vertex_groups) > 0:
			row = layout.row()
			if obj.vertex_groups.active.lock_weight:
				row.operator(LockUnusedVGs.bl_idname, text = 'Unlock', icon='LOCKED')
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
			
			split.prop(context.scene.tool_settings, 'vertex_group_weight', text = "Weight", slider = True)			
			if context.scene.tool_settings.vertex_group_weight > 0:
				split.operator("object.toggle_0_1_vertex_weight", text = "", icon = 'RADIOBUT_ON').value = 0.0
			else:
				split.operator("object.toggle_0_1_vertex_weight", text = "", icon = 'RADIOBUT_OFF').value = 1.0			
			
			column.operator("object.sync_vg", text = "Sync with Bones", icon='UV_SYNC_SELECT')

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

		column.operator("brush.draw_brush_template_settings", text = "Weight Paint 2D")

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
		
		layout.prop(bpy.context.scene, 'vertex_weight_input', slider = True)
		
		column = layout.column(align=True)
		split1 = column.split(factor=0.5, align=True)
		split1.operator("object.shift_weights", text = "Increase").action = True
		split1.operator("object.shift_weights", text = "Decrease").action = False
		
		split2 = column.split(factor=0.33, align=True)
		split2.operator("object.fill_active_vg", text = "Sel").only_selected = True
		split2.operator("object.fill_active_vg", text = "Act").only_selected = False
		split2.operator("object.fill_all_vg", text = "All")
		column.operator("object.clamp_near_zero_values", text = "Clamp")

class NormalsPanel(Panel):
	bl_label = "Normals"
	bl_idname = "OBJECT_PT_AUT_RIG_SK_NORMALS_PANEL"
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'	
	bl_category = "Automation Tools"
	bl_options =  {'DEFAULT_CLOSED'}
	bl_parent_id = ModelingPanel.bl_idname
	
	def draw(self, context):
		layout = self.layout
		column = layout.column(align=True)
			
		column.operator("mesh.customdata_custom_splitnormals_clear", text = "Split")
		column.operator("object.reset_normals_object", text = "Reset")

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

class CurvesPanel(Panel):
	bl_label = "Curves"
	bl_idname = "OBJECT_PT_AUT_RIG_SK_CURVES_PANEL"
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'	
	bl_category = "Automation Tools"
	bl_options =  {'DEFAULT_CLOSED'}
	bl_parent_id = ModelingPanel.bl_idname
	
	def draw(self, context):
		layout = self.layout
		column = layout.column(align=True)
		column.prop(bpy.context.scene, "curve_type")
		column.separator(factor=1.0)
		column.operator("object.curve_between_2_objects", text = "Vertices / Objects > Curve")		
		column.operator("object.edge_to_curve", text = "Edges > Curve")

class TriangulationPanel(Panel):
	bl_label = "Triangulation"
	bl_idname = "OBJECT_PT_AUT_RIG_SK_TRIANGULATION_PANEL"
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'	
	bl_category = "Automation Tools"
	bl_options =  {'DEFAULT_CLOSED'}
	bl_parent_id = ModelingPanel.bl_idname
	
	def draw(self, context):
		layout = self.layout
		column = layout.column(align=True)
		column.operator("mesh.rotate_edge_triangulation_quads", text = 'Rotate Edges Beauty').quad_method = 'BEAUTY'
		column.operator("mesh.rotate_edge_triangulation_quads", text = 'Rotate Edges Fixed').quad_method = 'FIXED_ALTERNATE'

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

		column.operator("object.add_bevel_width_driver", text = 'Lerp Bevel Width')			
		column.operator("view3d.toggle_all_modifiers_visibility", text = "Toggle All")
		column.operator("object.transfer_modifiers", text = "Transfer")
		column.operator("view3d.copy_apply_modifier", text = "Copy and Apply")
		column.operator("object.apply_modifiers_with_shape_keys", text = 'Apply [with Shape Keys]')

class StandardBatchExportPanel(Panel):
	bl_label = "Batch Export"
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

		split = column.split(factor=0.75, align=True)
		split.prop(bpy.context.scene, "hierarchy_list")
		split.operator("object.get_selected_objects_names", text = "Add")
		column.operator("object.fast_auto_fbx_export", text = "Export")
		column.prop(bpy.context.scene, "if_lods")

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

		column.operator("object.standard_batch_export", text = "Selected Objects")
		column.operator("object.fixture_export", text = "One Collection")
		column.operator("object.fixtures_batch_export", text = "All Collections")		

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

classes = (
	ActiveMeshPanel,
	ModesPanel,
	ModelingPanel,
	GeneratorsPanel,
	RiggingSkinningPanel,
	ExportPanel,
	UVsPanel,
	BonesPanel,
	VertexGroupsPanel,
	ShapeKeysPanel,
	BrushPanel,
	BrushAddSubPanel,
	BrushCustomizedSettingsPanel,
	WeightsPanel,
	NormalsPanel,
	CurvesPanel,
	ModifiersPanel,
	TriangulationPanel,
	LightsUVsPanel,
	MaterialsPanel,
	MaterialsAddPanel,
	MaterialsCleanupPanel,
	NamingPanel,
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
	SelectBonesMenu
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




	
