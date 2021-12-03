import bpy
import math
import webbrowser
from bpy.props import *

bl_info = {
    "name": "Automation Rim Generator",
    "description": "Automation Rim Generator",
    "author": "HardRooster",
    "version": (1, 0, 1),
    "blender": (2, 93, 5),
    "category": "3D View"
}

class CreateRim(bpy.types.Operator):
    """Adds a new rim project with new collections."""
    bl_idname = "object.rim_generator"
    bl_label = "Automation Tools Rim Creator"
    bl_options = {'REGISTER', 'UNDO'}
    bl_desription = "Automation Tools Rim Creator"

    # ----------------------------------------------------------------------------------

    # TODO: 1: Replace Empties with custom circular object that communicates better what's going on than the empty does.
    # TODO: 2: Fix LERP Functionality

    # ----------------------------------------------------------------------------------

    # Variable meant to be used globally as a counter to track vertex index as geometry is drawn.
    INDEX: IntProperty(
        options={'HIDDEN'},
        default=0,

    )

    INDEX_T: IntProperty(
        options={'HIDDEN'},
        default=0,

    )

    # Other fixed global variables that define rim dimensions and material colors.
    HUB_X = -0.043
    HUB_Y = 0.0
    HUB_Z = 0.0588
    HUB_X_BACK = 0.028
    RIM_X = -0.04434
    RIM_X_BACK = 0.0129
    RIM_X_TEMPLATE_FRONT = -0.15504
    RIM_X_TEMPLATE_BACK = -0.099833
    RIM_Z = 0.13
    RIM_Z_TEMPLATE = 0.36855
    MATERIAL_INDEX_ORDER = [2, 0, 1, 3, 1]
    MAT_COLORS = [
        (0.393, 0.393, 0.393, 1.0),  # Index 0, Color 1
        (0.036, 0.036, 0.036, 1.0),  # Index 1, Color 2
        (0.248, 0.393, 0.212, 1.0),  # Index 2, Color 3
        (0.066, 0.109, 0.174, 1.0),  # Index 3, Color 4
        (0.800, 0.408, 0.688, 1.0),  # Index 4, Color 5

    ]

    def __init__(self):
        self.mat_1_start = self.mat_2_start = self.mat_3_start = self.mat_4_start = self.mat_5_start = 0
        self.mat_start = [0, 0, 0, 0, 0]
        self.mat_1_end = self.mat_2_end = self.mat_3_end = self.mat_4_end = self.mat_5_end = 0
        self.mat_end = [0, 0, 0, 0, 0]
        self.smooth_1_start = self.smooth_2_start = self.smooth_3_start = 0
        self.smooth_start = [0, 0, 0]
        self.smooth_1_end = self.smooth_2_end = self.smooth_3_end = 0
        self.smooth_end = [0, 0, 0]
        self.collection_empty = None
        self.empty = None
        self.collection = None
        self.empty_nut = None
        self.collection_already_exists = False

    def rim_geometry_generator(self, spin, pos_x, pos_y, pos_z, bool_faces, bool_append, verts, faces):
        """Draws one pass of quad geometry, takes spin, x, y and z positions for a single vertex, will work out where
        to place the rest of them, bool for whether or not to draw faces, bool for something else :P, the verts and
        faces lists."""
        verts.append(  # Index n
            [  # List
                pos_x,
                pos_y,
                pos_z
            ]
        )

        self.INDEX = self.INDEX + 1
        for index in range(self.subs):
            new_spin = spin / self.subs
            new_index = index + 1
            angle = math.radians(new_spin * new_index)
            new_pos_y = math.sin(angle) * pos_z
            new_pos_z = math.cos(angle) * pos_z
            verts.append(
                [
                    pos_x,
                    new_pos_y,
                    new_pos_z
                ]
            )
            if bool_append:
                self.INDEX = self.INDEX + 1
                if bool_faces or not bool_faces and self.subs - self.spoke > index:
                    faces.append(
                        [  # Works out which verts to append to create faces
                            self.INDEX - self.subs - 1,
                            self.INDEX - self.subs - 2,
                            self.INDEX - 1,
                            self.INDEX
                        ]
                    )
            elif not bool_append:
                self.INDEX = self.INDEX + 1

    @staticmethod
    def deselect_all():
        """Deselects all verts, records mode, and select_mode and returns to the
        pre-existing state before the method was called"""
        mode_is = bpy.context.active_object.mode

        if mode_is != 'EDIT':
            bpy.ops.object.mode_set(mode='EDIT', toggle=True)

        select_mode_check = bpy.context.tool_settings.mesh_select_mode
        if not select_mode_check[0] and not select_mode_check[1] and select_mode_check[2]:
            select_mode_is = 'FACE'
        elif not select_mode_check[0] and select_mode_check[1] and not select_mode_check[2]:
            select_mode_is = 'EDGE'
        else:
            select_mode_is = 'VERT'

        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.mesh.select_mode(type=select_mode_is)
        bpy.ops.object.mode_set(mode=mode_is, toggle=True)

    @staticmethod
    def enable_vertex_select_mode():
        mode_is = bpy.context.active_object.mode

        if mode_is != 'EDIT':
            bpy.ops.object.mode_set(mode='EDIT', toggle=True)
        bpy.ops.mesh.select_mode(type='VERT')
        bpy.ops.object.mode_set(mode=mode_is, toggle=True)

    @staticmethod
    def set_object_mode():
        try:
            mode_is = None
            obj = bpy.context.active_object
            if obj:
                mode_is = bpy.context.active_object.mode

            if mode_is is not None and mode_is != 'OBJECT':
                bpy.ops.object.mode_set(mode='OBJECT', toggle=True)

        except AttributeError:
            self.report({'WARNING'},  "No object selected")
            pass

    @staticmethod
    def set_edit_mode():
        try:
            mode_is = bpy.context.active_object.mode

            if mode_is != 'EDIT':
                bpy.ops.object.mode_set(mode='EDIT', toggle=True)

        except AttributeError:
            self.report({'WARNING'},  "No object selected")
            pass

    @staticmethod
    def material_assignments(self, start, stop, mat_index, colors):
        """Assigns materials to specific faces, also assigns viewport colors"""
        obj = bpy.context.object
        bops = bpy.ops
        mesh = obj.data

        for i in range(start, stop):
            mesh.vertices[i].select = True

        bops.object.mode_set(mode='EDIT')
        obj.active_material_index = mat_index
        bops.object.material_slot_assign()
        bops.object.mode_set(mode='OBJECT')
        if self.view_colors:
            bpy.context.object.active_material.diffuse_color = colors[mat_index]

        self.deselect_all()

    @staticmethod
    def smooth(self, start, stop):
        """Smooths selected faces"""
        obj = bpy.context.object
        mesh = obj.data
        bops = bpy.ops
        mode_is = bpy.context.active_object.mode

        for i in range(start, stop):
            mesh.vertices[i].select = True

        if mode_is != 'EDIT':
            bops.object.mode_set(mode='EDIT')
        bops.mesh.faces_shade_smooth()
        bops.object.mode_set(mode='OBJECT')

        self.deselect_all()

    @staticmethod
    def check_add_materials(self, new_mesh, colors):
        """Checks the blend file to see if materials for the rim exist, and if not, adds them."""
        mat_names = [
            'Wheel_Primary',  # Index 0
            'Wheel_Secondary',  # Index 1
            'Wheel_Misc1',  # Index 2
            'Wheel_Misc2',  # Index 3
            'Wheel_Nuts_Misc3',  # Index 4

        ]

        materials = []

        for mats in range(len(mat_names)):
            #print(mats)
            try:
                materials.append(bpy.data.materials[mat_names[mats]])
            except KeyError:
                materials.append(bpy.data.materials.new(name=mat_names[mats]))
                materials[mats].use_nodes = True
                nodes = materials[mats].node_tree.nodes
                bsdf = nodes.get('Principled BSDF')
                bsdf.inputs[0].default_value = colors[mats]

            #print(materials[mats])
            #print(colors[mats])

            new_mesh.data.materials.append(materials[mats])

    def build_rim(self, spin, verts, faces):
        """Assembles the vertex geometry and fills in faces"""
        # Place first vertex and begin building the mesh
        # Places vert index 0 at the center hub vert, this is fixed and unchanging.
        verts.append([  # Index 0
            self.HUB_X - (self.cap_protrusion / 1000),
            0.0,
            0.0
        ])
        self.INDEX = 0
        self.mat_start[0] = self.INDEX

        # ----------------------------------------------------------------------------------

        # Builds initial triangular geometry.
        verts.append(
            [  # index 1
                self.HUB_X - (self.cap_protrusion / 1000),
                self.HUB_Y,
                self.HUB_Z / self.cap_size,

            ]
        )
        self.INDEX = self.INDEX + 1

        for index in range(self.subs):
            index_y = index + 1
            index_z = index_y + 1
            new_spin = spin / self.subs
            verts.append(
                [
                    self.HUB_X - (self.cap_protrusion / 1000),
                    math.sin(math.radians(new_spin * (index + 1))) * self.HUB_Z / self.cap_size,
                    math.cos(math.radians(new_spin * (index + 1))) * self.HUB_Z / self.cap_size
                ]
            )
            self.INDEX = self.INDEX + 1
            faces.append([0, index_y, index_z])

        # Quad Geometry function calls
        self.mat_start[1] = self.INDEX + 1
        self.smooth_start[0] = 1
        self.rim_geometry_generator(
            spin,
            (self.HUB_X + .0015),
            self.HUB_Y,
            ((self.HUB_Z * 1.03) / self.cap_size),
            True,
            True,
            verts,
            faces,

        )
        self.mat_end[0] = self.INDEX + 1
        self.smooth_start[1] = self.INDEX + 1
        self.rim_geometry_generator(
            spin,
            self.HUB_X,
            self.HUB_Y,
            ((self.HUB_Z * 1.06) / self.cap_size),
            True,
            True,
            verts,
            faces,

        )
        self.smooth_end[0] = self.INDEX + 1
        # Line below draws the outer hub boundary, make sure it's fixed
        self.rim_geometry_generator(
            spin,
            self.HUB_X,
            self.HUB_Y,
            self.HUB_Z,
            True,
            True,
            verts,
            faces,

        )
        self.rim_geometry_generator(
            spin,
            (self.RIM_X + (self.rim_depth / 400)),
            self.HUB_Y,
            (((self.RIM_Z - self.HUB_Z) * (1 / 3)) + self.HUB_Z),
            False,
            True,
            verts,
            faces,

        )
        self.rim_geometry_generator(
            spin,
            (self.RIM_X + (self.rim_depth / 200)),
            self.HUB_Y,
            (((self.RIM_Z - self.HUB_Z) * (2 / 3)) + self.HUB_Z),
            False,
            True,
            verts,
            faces,

        )
        self.mat_start[2] = self.INDEX + 1
        self.rim_geometry_generator(
            spin,
            (self.RIM_X + (self.rim_depth / 100)),
            self.HUB_Y,
            (self.RIM_Z - .008),
            False,
            True,
            verts,
            faces,

        )
        self.mat_end[1] = self.INDEX + 1
        self.mat_start[3] = self.INDEX + 1
        self.rim_geometry_generator(
            spin,
            self.RIM_X,
            self.HUB_Y,
            (self.RIM_Z - .008),
            True,
            True,
            verts,
            faces,

        )
        self.smooth_end[1] = self.INDEX + 1
        self.mat_end[2] = self.INDEX + 1
        self.smooth_start[2] = self.INDEX + 1
        # Line below draws the outer rim boundary, make sure it's fixed
        self.rim_geometry_generator(
            spin,
            self.RIM_X,
            self.HUB_Y,
            self.RIM_Z,
            True,
            True,
            verts,
            faces,

        )
        # Line below draws the inner rim boundary, make sure it's fixed
        self.rim_geometry_generator(
            spin,
            self.RIM_X_BACK,
            self.HUB_Y,
            self.RIM_Z,
            True,
            True,
            verts,
            faces,

        )
        # self.smooth_end[2] = self.INDEX + 1
        self.mat_end[3] = self.INDEX + 1
        # Lines below draw the hub and select for material assignment
        self.mat_start[4] = self.INDEX + 1
        self.rim_geometry_generator(
            spin,
            (self.HUB_X + (self.thick / 100)),
            self.HUB_Y,
            self.HUB_Z,
            True,
            False,
            verts,
            faces,

        )
        self.rim_geometry_generator(
            spin,
            self.HUB_X + .071045,
            self.HUB_Y,
            self.HUB_Z,
            True,
            True,
            verts,
            faces,

        )
        self.mat_end[4] = self.INDEX + 1
        self.smooth_end[2] = self.INDEX + 1

    @staticmethod
    def create_collection_empties():
        """Creates the empties collection if one doesn't already exist, returns collection_empty"""
        collection_empty = bpy.context.blend_data.collections.new(name='Empties - Do Not Delete')
        bpy.context.collection.children.link(collection_empty)
        return collection_empty

    @staticmethod
    def create_project_collection():
        """Creates the rim collection, returns collection"""
        collection = bpy.context.blend_data.collections.new(name='Automation Rim Project')
        bpy.context.collection.children.link(collection)
        return collection

    def spawn_rim_empty(self, spin):
        """Creates the rim empty, put it in the empties collection and unlink data, returns empty"""
        # self.collection_empty.get("Empties - Do Not Delete")
        bpy.ops.object.empty_add(
            type='PLAIN_AXES',
            align='WORLD'
        )
        empty = bpy.context.active_object
        empty.rotation_euler[0] += math.radians(spin * 2)
        empty.name = "Rim Spinner - Do Not Delete"
        self.collection_empty.objects.link(empty)
        bpy.context.collection.objects.unlink(empty)
        bpy.context.active_object.select_set(False)
        bpy.context.object.hide_set(True)
        return empty

    def spawn_nut_empty(self, spin_nut):
        # Create the lug nut empty, put it in the empties collection and unlink data
        bpy.ops.object.empty_add(
            type='PLAIN_AXES',
            align='WORLD',

        )
        empty_nut = bpy.context.active_object
        empty_nut.rotation_euler[0] += (math.radians(spin_nut * 2) + (math.radians(self.lug_spin * - 1)))
        empty_nut.name = "Lug Nut Spinner - Do Not Delete"
        self.collection_empty.objects.link(empty_nut)
        bpy.context.collection.objects.unlink(empty_nut)
        bpy.context.active_object.select_set(False)
        bpy.context.object.hide_set(True)
        return empty_nut

    def assign_materials_to_object(self):
        for i in range(5):
            self.material_assignments(
                self,
                self.mat_start[i],
                self.mat_end[i],
                self.MATERIAL_INDEX_ORDER[i],
                self.MAT_COLORS
            )

    def smooth_faces(self):
        """Smooth faces selectively"""
        for i in range(3):
            self.smooth(self, self.smooth_start[i], self.smooth_end[i])

    def smooth_all(self):
        self.set_edit_mode()
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.faces_shade_smooth()
        self.set_object_mode()

    def excess_vert_delete(self, second_vert_start, end_vert):
        # Delete unneeded verts in case of no spoke
        start_vert_update = second_vert_start - self.spoke
        second_vert_start_update = end_vert - self.spoke

        if self.subs > self.spoke:
            for i in range(start_vert_update, second_vert_start):
                bpy.context.object.data.vertices[i].select = True
            for i in range(second_vert_start_update, end_vert):
                bpy.context.object.data.vertices[i].select = True

            mode_is = bpy.context.active_object.mode
            if mode_is != 'EDIT':
                bpy.ops.object.mode_set(mode='EDIT', toggle=True)
            bpy.ops.mesh.delete(type='VERT')
            bpy.ops.object.mode_set(mode=mode_is, toggle=True)

    def sharpen_edges(self, start_vert, vert_quantity):
        # Sharpen selected edges
        for i in range((start_vert - (vert_quantity - (self.subs + 1))), (start_vert - self.spoke)):
            bpy.context.object.data.vertices[i].select = True

        mode_is = bpy.context.active_object.mode
        if mode_is != 'EDIT':
            bpy.ops.object.mode_set(mode='EDIT', toggle=True)
        bpy.ops.mesh.mark_sharp()
        bpy.ops.object.mode_set(mode=mode_is, toggle=True)

    def extrude_rim_thickness(self, start_vert, vert_quantity):
        # Select and extrude rim
        if self.spoke > 0:
            point_a = start_vert - vert_quantity + self.spoke - (self.subs * 2) - 2
            point_b = start_vert + self.subs - self.spoke
            point_c = point_b + self.subs - self.spoke + 1
            point_d = point_c + self.subs - self.spoke + 1
            point_e = point_d + point_a

            for i in range((start_vert - point_a), start_vert):
                bpy.context.object.data.vertices[i].select = True

            bpy.context.object.data.vertices[point_b].select = True
            bpy.context.object.data.vertices[point_c].select = True

            for i in range(point_d, point_e):
                bpy.context.object.data.vertices[i].select = True

        mode_is = bpy.context.active_object.mode
        if mode_is != 'EDIT':
            bpy.ops.object.mode_set(mode='EDIT')

        # Extrude
        thickness = self.thick / 100
        bpy.ops.mesh.extrude_region_move(TRANSFORM_OT_translate={"value": (thickness, 0, 0)})
        # Selecting additional loop and adding material to extrusion
        bpy.ops.mesh.select_more()
        bpy.context.object.active_material_index = 1
        bpy.ops.object.material_slot_assign()

    @staticmethod
    def add_mirror_modifier(obj):
        # mirror modifier
        mod_mirror = obj.modifiers.new("Mirror", 'MIRROR')
        mod_mirror.use_axis[0] = False
        mod_mirror.use_axis[1] = True
        mod_mirror.merge_threshold = 0.00001
        mod_mirror.use_clip = False
        return mod_mirror

    @staticmethod
    def add_array_modifier(obj, array_elements, empty):
        # array modifier
        mod_array = obj.modifiers.new("Array", 'ARRAY')
        mod_array.count = array_elements
        mod_array.use_relative_offset = False
        mod_array.use_object_offset = True
        mod_array.offset_object = empty
        mod_array.use_merge_vertices = True
        mod_array.merge_threshold = 0.00001
        mod_array.use_merge_vertices_cap = True
        return mod_array

    @staticmethod
    def add_bevel_modifier(obj, bevel_amount, bevel_limit, bevel_limit_amount):
        # bevel modifier
        mod_bevel = obj.modifiers.new("Bevel", 'BEVEL')
        mod_bevel.width = bevel_amount
        mod_bevel.segments = 2
        mod_bevel.limit_method = bevel_limit
        mod_bevel.angle_limit = bevel_limit_amount
        return mod_bevel

    @staticmethod
    def add_tri_modifier(obj):
        # triangulate modifier
        mod_tri = obj.modifiers.new("Triangulate", 'TRIANGULATE')
        mod_tri.show_viewport = False
        mod_tri.quad_method = 'FIXED'

    def spawn_lug_nuts(self, lug_span, col):
        span = lug_span / 100
        bpy.ops.mesh.primitive_cylinder_add(
            vertices=6,
            depth=0.009,
            radius=0.007,
            enter_editmode=False,
            align='WORLD',
            location=[-0.047, 0, span],
            rotation=[0, 1.5708, 0],
            scale=[1, 1, 1]
        )
        nuts = bpy.context.active_object
        nuts.name = "Lug Nuts"
        #  Code recently added, could be problem area...
        if self.new_collection:
            col.get("Automation Rim Project")
            try:
                col.objects.link(nuts)
            except RuntimeError:                
                self.report({'WARNING'},  "Lug Nut object already linked to collection")
            bpy.context.collection.objects.unlink(nuts)
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        # rotates lug nuts with lugSpin variable to create a lug nut offset.
        bpy.ops.transform.rotate(
            value=(math.radians(self.lug_spin * - 1)),
            orient_axis='X',
            orient_type='GLOBAL',
            orient_matrix=[
                (1, 0, 0),
                (0, 1, 0),
                (0, 0, 1)
            ],
            orient_matrix_type='GLOBAL',
            constraint_axis=[True, False, False],
            mirror=True,
            use_proportional_edit=False,
            proportional_edit_falloff='SMOOTH',
            proportional_size=0.00937039,
            use_proportional_connected=False,
            use_proportional_projected=False
        )
        self.deselect_all()
        nuts.data.polygons[4].select = True
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.delete(type='FACE')
        bpy.ops.object.mode_set(mode='OBJECT')
        nuts.data.polygons[6].select = True
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.inset(thickness=0.00192493, depth=0)
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
        bpy.ops.mesh.subdivide()
        bpy.context.scene.tool_settings.transform_pivot_point = 'BOUNDING_BOX_CENTER'
        bpy.ops.transform.tosphere(
            value=1,
            mirror=True,
            use_proportional_edit=False,
            proportional_edit_falloff='SMOOTH',
            proportional_size=0.00937039,
            use_proportional_connected=False,
            use_proportional_projected=False
        )
        bpy.ops.mesh.extrude_region_move(
            MESH_OT_extrude_region={"use_normal_flip": False,
                                    "use_dissolve_ortho_edges": False,
                                    "mirror": False},
            TRANSFORM_OT_translate={"value": (0, 0, 0.00168543),
                                    "orient_type": 'NORMAL',
                                    "orient_matrix": (
                                        (2.36401e-06, 0.707107, 0.707106), (-2.19138e-06, 0.707106, -0.707107),
                                        (-1, 1.22077e-07, 3.22115e-06)),
                                    "orient_matrix_type": 'NORMAL', "constraint_axis": (False, False, True),
                                    "mirror": False,
                                    "use_proportional_edit": False,
                                    "proportional_edit_falloff": 'SMOOTH',
                                    "proportional_size": 0.00937039,
                                    "use_proportional_connected": False,
                                    "use_proportional_projected": False,
                                    "snap": False,
                                    "snap_target": 'CLOSEST',
                                    "snap_point": (0, 0, 0),
                                    "snap_align": False,
                                    "snap_normal": (0, 0, 0),
                                    "gpencil_strokes": False,
                                    "cursor_transform": False,
                                    "texture_space": False,
                                    "remove_on_cancel": False,
                                    "release_confirm": False,
                                    "use_accurate": False,
                                    "use_automerge_and_split": False}
        )
        bpy.ops.mesh.extrude_region_move(
            MESH_OT_extrude_region={"use_normal_flip": False,
                                    "use_dissolve_ortho_edges": False,
                                    "mirror": False},
            TRANSFORM_OT_translate={"value": (0, 0, 0.00174559),
                                    "orient_type": 'NORMAL',
                                    "orient_matrix": (
                                        (2.10505e-06, 0.707107, 0.707106), (-2.45034e-06, 0.707106, -0.707107),
                                        (-1, -2.44153e-07, 3.22114e-06)),
                                    "orient_matrix_type": 'NORMAL',
                                    "constraint_axis": (False, False, True),
                                    "mirror": False,
                                    "use_proportional_edit": False,
                                    "proportional_edit_falloff": 'SMOOTH',
                                    "proportional_size": 0.00937039,
                                    "use_proportional_connected": False,
                                    "use_proportional_projected": False,
                                    "snap": False,
                                    "snap_target": 'CLOSEST',
                                    "snap_point": (0, 0, 0),
                                    "snap_align": False,
                                    "snap_normal": (0, 0, 0),
                                    "gpencil_strokes": False,
                                    "cursor_transform": False,
                                    "texture_space": False,
                                    "remove_on_cancel": False,
                                    "release_confirm": False,
                                    "use_accurate": False,
                                    "use_automerge_and_split": False}
        )
        bpy.ops.transform.resize(
            value=[1, 0.778713, 0.778713],
            orient_type='GLOBAL',
            orient_matrix=[(1, 0, 0), (0, 1, 0), (0, 0, 1)],
            orient_matrix_type='GLOBAL',
            constraint_axis=[False, True, True],
            mirror=True,
            use_proportional_edit=False,
            proportional_edit_falloff='SMOOTH',
            proportional_size=0.00937039,
            use_proportional_connected=False,
            use_proportional_projected=False
        )
        bpy.ops.mesh.extrude_region_move(
            MESH_OT_extrude_region={"use_normal_flip": False,
                                    "use_dissolve_ortho_edges": False,
                                    "mirror": False},
            TRANSFORM_OT_translate={"value": (0, 0, 0.00151651),
                                    "orient_type": 'NORMAL',
                                    "orient_matrix": (
                                        (3.20965e-06, 0.707107, 0.707107), (-2.64024e-06, 0.707107, -0.707107),
                                        (-1, 4.02631e-07, 4.1365e-06)),
                                    "orient_matrix_type": 'NORMAL',
                                    "constraint_axis": (False, False, True),
                                    "mirror": False,
                                    "use_proportional_edit": False,
                                    "proportional_edit_falloff": 'SMOOTH',
                                    "proportional_size": 0.00937039,
                                    "use_proportional_connected": False,
                                    "use_proportional_projected": False,
                                    "snap": False, "snap_target": 'CLOSEST',
                                    "snap_point": (0, 0, 0),
                                    "snap_align": False,
                                    "snap_normal": (0, 0, 0),
                                    "gpencil_strokes": False,
                                    "cursor_transform": False,
                                    "texture_space": False,
                                    "remove_on_cancel": False,
                                    "release_confirm": False,
                                    "use_accurate": False,
                                    "use_automerge_and_split": False}
        )
        bpy.ops.transform.resize(
            value=[1, 0.425487, 0.425487],
            orient_type='GLOBAL',
            orient_matrix=[(1, 0, 0), (0, 1, 0), (0, 0, 1)],
            orient_matrix_type='GLOBAL',
            constraint_axis=[False, True, True],
            mirror=True,
            use_proportional_edit=False,
            proportional_edit_falloff='SMOOTH',
            proportional_size=0.00937039,
            use_proportional_connected=False,
            use_proportional_projected=False
        )
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.transform.rotate(
            value=(math.radians(self.lug_rot)),
            orient_axis='X',
            orient_type='GLOBAL',
            orient_matrix=[(1, 0, 0), (0, 1, 0), (0, 0, 1)],
            orient_matrix_type='GLOBAL',
            constraint_axis=[True, False, False],
            mirror=True,
            use_proportional_edit=False,
            proportional_edit_falloff='SMOOTH',
            proportional_size=0.00937039,
            use_proportional_connected=False,
            use_proportional_projected=False
        )
        bpy.ops.object.mode_set(mode='OBJECT')

        return nuts

    def assign_single_material_to_whole_mesh(self):
        self.set_object_mode()
        ob = bpy.context.active_object
        mat = bpy.data.materials.get('Wheel_Nuts_Misc3')
        bpy.ops.object.editmode_toggle()
        bpy.ops.mesh.select_all(action='SELECT')
        ob.data.materials.append(mat)
        bpy.ops.object.material_slot_assign()
        self.set_object_mode()
        if self.view_colors:
            bpy.context.object.active_material.diffuse_color = self.MAT_COLORS[4]

    def current_subs(self, context):
        if self.spoke >= (self.subs - 1):
            self.spoke = (self.subs - 1)

    def current_thick(self, context):
        if self.rim_depth + self.thick >= 5.80:
            self.thick = 5.8 - self.rim_depth

    def traverse_tree(self, t):
        yield t
        for child in t.children:
            yield from self.traverse_tree(child)

    def template_geometry_generator(self, total_circle_verts, spin, pos_x, pos_y, pos_z, bool_faces, bool_append, verts,
                                    faces):
        """Draws one pass of quad geometry, takes spin, x, y and z positions for a single vertex, will work out where
        to place the rest of them, bool for whether or not to draw faces, bool for something else :P, the verts and
        faces lists."""
        verts.append(  # Index n
            [  # List
                pos_x,
                pos_y,
                pos_z
            ]
        )

        self.INDEX_T += 1
        for index in range(total_circle_verts):
            new_spin = spin / self.subs
            new_index = index + 1
            angle = math.radians(new_spin * new_index)
            new_pos_y = math.sin(angle) * pos_z
            new_pos_z = math.cos(angle) * pos_z
            verts.append(
                [
                    pos_x,
                    new_pos_y,
                    new_pos_z
                ]
            )
            if bool_append:
                if bool_faces:
                    faces.append(
                        [  # Works out which verts to append to create faces
                            self.INDEX_T + total_circle_verts + 1,
                            self.INDEX_T + total_circle_verts,
                            self.INDEX_T - 1,
                            self.INDEX_T
                        ]
                    )
                self.INDEX_T += 1
            else:
                self.INDEX_T += 1

    def add_custom_template(self, spin):
        # Variables
        verts_t, edges_t, faces_t = [], [], []
        total_verts_in_circle = self.subs * self.array_elements * 2

        self.set_object_mode()
        # Place first vertex and begin building the mesh
        # Places vert index 0 at the center hub vert, this is fixed and unchanging.
        verts_t.append([  # Index 0
            self.HUB_X,
            0.0,
            0.0
        ])
        self.INDEX_T = 0

        # verts_t.append([.1, .1, .1])

        # Builds initial triangular geometry.
        verts_t.append(
            [  # index 1
                self.HUB_X,
                self.HUB_Y,
                self.HUB_Z,

            ]
        )
        self.INDEX_T += 1

        for index in range(total_verts_in_circle):
            index_y = index + 1
            index_z = index_y + 1
            new_spin = (spin / self.subs)
            verts_t.append(
                [
                    self.HUB_X,
                    math.sin(math.radians(new_spin * (index + 1))) * self.HUB_Z,
                    math.cos(math.radians(new_spin * (index + 1))) * self.HUB_Z
                ]
            )
            self.INDEX = self.INDEX + 1
            faces_t.append([0, index_y, index_z])

        # Quad Geometry function calls
        self.template_geometry_generator(
            total_verts_in_circle,
            spin,
            self.HUB_X + .071045,
            self.HUB_Y,
            self.HUB_Z,
            True,
            True,
            verts_t,
            faces_t
        )
        self.template_geometry_generator(
            total_verts_in_circle,
            spin,
            self.RIM_X,
            self.HUB_Y,
            self.RIM_Z,
            False,
            True,
            verts_t,
            faces_t
        )
        self.template_geometry_generator(
            total_verts_in_circle,
            spin,
            self.RIM_X_BACK,
            self.HUB_Y,
            self.RIM_Z,
            True,
            True,
            verts_t,
            faces_t
        )
        self.template_geometry_generator(
            total_verts_in_circle,
            spin,
            self.RIM_X_TEMPLATE_FRONT,
            self.HUB_Y,
            self.RIM_Z,
            False,
            True,
            verts_t,
            faces_t
        )
        self.template_geometry_generator(
            total_verts_in_circle,
            spin,
            self.RIM_X_TEMPLATE_BACK,
            self.HUB_Y,
            self.RIM_Z,
            True,
            True,
            verts_t,
            faces_t
        )
        self.template_geometry_generator(
            total_verts_in_circle,
            spin,
            self.RIM_X,
            self.HUB_Y,
            self.RIM_Z_TEMPLATE,
            False,
            True,
            verts_t,
            faces_t
        )
        self.template_geometry_generator(
            total_verts_in_circle,
            spin,
            self.RIM_X_BACK,
            self.HUB_Y,
            self.RIM_Z_TEMPLATE,
            True,
            True,
            verts_t,
            faces_t
        )

        name_t = "Automation Rim Template"  # Create rim template name
        mesh_t = bpy.data.meshes.new(name_t)  # Create rim template mesh
        obj_t = bpy.data.objects.new(name_t, mesh_t)  # Create rim template object

        col = bpy.context.collection
        col.objects.link(obj_t)
        mesh_t.from_pydata(verts_t, edges_t, faces_t)  # Creates actual geometry

    wire: BoolProperty(
        name="Wireframe",
        description="Shows/Hides wireframe mode",
        default=True,

    )

    array_visibility: BoolProperty(
        name="Array Visibility",
        description="Shows/Hides the Array Modifier",
        default=True,

    )
    mirror_visibility: BoolProperty(
        name="Mirror Visibility",
        description="Shows/Hides the Mirror Modifier",
        default=True,

    )
    array_elements: IntProperty(
        name="Pie Slices (Spokes)",
        description="Splits the rim into a number of 'spokes' or 'pie slices'",
        default=5,
        min=2,
        max=24,

    )
    subs: IntProperty(
        name="Subdivisions",
        description="Splits each individual 'spoke' or 'pie slice' into more slices",
        default=12,
        min=1,
        max=48,
        update=current_subs,

    )
    spoke: IntProperty(
        name="Spoke Size",
        description="Enlarges spokes to help visualize rim elements",
        default=8,
        min=0,
        max=46,
        update=current_subs,

    )
    rim_depth: FloatProperty(
        name="Rim Depth",
        description="Sets the depth of the rim at the outer edge",
        default=2.0,
        min=0.1,
        max=4.0,
        update=current_thick,

    )
    thick: FloatProperty(
        name="Thickness",
        description="Thickness of Rim Extrusion",
        default=2.00,
        min=0.5,
        max=3.5,
        update=current_thick,

    )
    cap_size: FloatProperty(
        name="Center Cap Diameter",
        description="Changes the size of the center cap",
        default=3.0,
        min=1.65,
        max=7.0,

    )
    cap_protrusion: FloatProperty(
        name="Center Cap Thickness",
        description="Gives the center cap a bit of protrusion",
        default=1.0,
        min=0.0,
        max=6.0,

    )
    lugs: BoolProperty(
        name="Lug Nuts",
        description="Enable and Disable lug nuts",

    )
    lugs_num: IntProperty(
        name="Lug Nuts",
        description="Inserts Lug Nuts",
        default=4,
        min=3,
        max=10,

    )
    lug_rot: FloatProperty(
        name="Lug Nut Rotation",
        description="Rotates the lug nut individually to crate random tightening appearance",
        default=0.0,
        min=0.0,
        max=59.0,

    )
    lug_spin: FloatProperty(
        name="Lug Nut Spin Offset",
        description="Offsets lug not rotation around the middle",
        default=0.0,
        min=0.0,
        max=119.0,

    )
    lug_span: FloatProperty(
        name="Lug Nut Span",
        description="Moves lug nuts closer together, or further apart",
        default=3.8,
        min=2.0,
        max=12.0,

    )
    view_colors: BoolProperty(
        name="Update Viewport Colors?",
        description="Will add the material colors to the viewport display colors of materials.",
        default=False,

    )
    new_collection: BoolProperty(
        name="Add to new Collection",
        description="Add to a new collection in your selected collection, or add to selected collection directly.",
        default=True,

    )
    add_template: BoolProperty(
        name="Add Custom Template?",
        description="Adds a rim template based on your mesh density so when scaling later, the edges align.",
        default=False,

    )

    # Main script begins
    def execute(self, context):

        # Variables
        spin = 180 / self.array_elements
        spin_nut = 180 / self.lugs_num
        verts, edges, faces = [], [], []
        vert_quantity = 2 + (self.subs * 2)
        start_vert = (5 + (self.subs * 4))
        end_vert = (start_vert + vert_quantity)
        second_vert_start = ((end_vert - start_vert) + 1) / 2 + start_vert
        second_vert_start = int(second_vert_start)
        all_collections = bpy.context.scene.collection

        self.set_object_mode()
        bpy.context.scene.tool_settings.use_mesh_automerge = False  # Turn off auto-merge
        self.build_rim(spin, verts, faces)  # Creates mesh data (method call)

        if all_collections is not None:  # Safety Check, probably unneeded.
            for c in self.traverse_tree(all_collections):  # Not exactly sure how this method works from Stack Exchange.
                if c.name == 'Empties - Do Not Delete':  # Checking if the Empties folder already exists.
                    self.collection_empty = c  # Sets the variable to the existing collection
                    self.collection_already_exists = True
        if not self.collection_already_exists:  # Makes a new Empties folder.
            self.collection_empty = self.create_collection_empties()  # Creates empty collection (method call)

        self.empty = self.spawn_rim_empty(spin)  # Creates rim empty (method call)
        name = "Automation Rim"  # Create rim name
        mesh = bpy.data.meshes.new(name)  # Create rim mesh
        obj = bpy.data.objects.new(name, mesh)  # Create rim object

        if self.new_collection:  # Checks if Add New Collection box is ticked
            self.collection = self.create_project_collection()  # Creates rim collection (method call)
            col = self.collection
            col.objects.link(obj)  # Links new object to collection
        else:  # If not, links object to active collection, and assigns the active collection to the col variable.
            bpy.context.collection.objects.link(obj)
            col = bpy.context.collection

        bpy.context.view_layer.objects.active = obj
        mesh.from_pydata(verts, edges, faces)  # Creates actual geometry
        self.check_add_materials(self, obj, self.MAT_COLORS)  # Adds materials if needed to blend file (method call)
        self.enable_vertex_select_mode()
        self.deselect_all()
        self.assign_materials_to_object()  # Assigns materials to object (method call)
        bpy.context.object.data.use_auto_smooth = True  # Turns on auto-smooth
        self.smooth_faces()
        self.excess_vert_delete(second_vert_start, end_vert)  # Deletes excess verts in case of no spoke
        self.sharpen_edges(start_vert, vert_quantity)  # Sharpens select edges
        self.deselect_all()
        self.extrude_rim_thickness(start_vert, vert_quantity)
        self.deselect_all()
        mod_mirror = self.add_mirror_modifier(obj)  # Adds mirror modifier, return
        mod_array = self.add_array_modifier(obj, self.array_elements, self.empty)  # Adds array modifier, returns

        rim_bevel_amount = 0.001
        rim_bevel_limit = 'WEIGHT'
        rim_bevel = self.add_bevel_modifier(obj, rim_bevel_amount, rim_bevel_limit, 0)  # Adds Bevel modifier, returns
        self.add_tri_modifier(obj)  # Adds Triangulate modifiers

        # ----------------------------------------------------------------------------------

        # Adds custom wheel template.
        if self.add_template:
            self.add_custom_template(spin)

        # ----------------------------------------------------------------------------------

        # Build Lug nut from empty cylinder primitive
        if self.lugs:
            self.empty_nut = self.spawn_nut_empty(spin_nut)  # Creates lug nut empty (method call)
            nuts = self.spawn_lug_nuts(self.lug_span, col)  # Spawns lug nuts if the box is ticked.

            # Adds Modifiers and set variables as needed
            nut_bevel_amount = 0.0004
            nut_bevel_limit = 'ANGLE'
            nut_bevel_limit_amount = 0.785398
            nut_bevel = self.add_bevel_modifier(nuts, nut_bevel_amount, nut_bevel_limit, nut_bevel_limit_amount)
            self.add_array_modifier(nuts, self.lugs_num, self.empty_nut)
            self.assign_single_material_to_whole_mesh()
            self.smooth_all()
        elif not self.lugs:
            self.report({'WARNING'},  "lug nuts off")
            # We likely can remove this elif statement if it's not needed for other functions later.

        # ----------------------------------------------------------------------------------

        # Menu visibility toggles
        bpy.context.space_data.overlay.show_wireframes = self.wire
        mod_array.show_viewport = self.array_visibility
        mod_mirror.show_viewport = self.mirror_visibility

        return {'FINISHED'}


#classes = (
#    CreateRim
#)


#def register():
#    for cls in classes:
#        bpy.utils.register_class(cls)

#def unregister():
#    for cls in reversed(classes):
#        bpy.utils.unregister_class(cls)

def register(): 
    bpy.utils.register_class(CreateRim)
    
def unregister():
    bpy.utils.unregister_class(CreateRim)