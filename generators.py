bl_info = {
    "name": "Automation Rim Generator",
    "description": "Automation Rim Generator",
    "author": "HardRooster",
    "version": (1, 0, 0),
    "blender": (2, 92, 0),
    "category": "3D View"
}

import bpy
import math
import sys
from bpy.props import *
from bpy.types import Operator

class AddRim(bpy.types.Operator):
    bl_idname = "object.rim_generator_add_mesh"
    bl_label = "Automation Tools Rim Mesh Adder"
    bl_options = {'REGISTER', 'UNDO'}  
    
    print("Do Stuff")      

    
class CreateRim(bpy.types.Operator):
    bl_idname = "object.rim_generator"
    bl_label = "Automation Tools Rim Creator"
    bl_options = {'REGISTER', 'UNDO'}
        
    ########################################################################################    
            
    #TODOs
    #figure out custom function for material properties
    #figure out custom function for deselect all in object mode
    #Give an option for adding new rim components to existing project, or create a new folder
    #Create function for adjusting bevel with a driver, driven by empty coordinates
    #fix empty for lugnuts appearing without lugnuts
    #Clean up excess code
    
    ########################################################################################
    
    #create pop up menu properties with custom functions to keep them in bounds
       
    def currentSubs(self, context):
        if self.spoke >= (self.subs - 1):
            self.spoke = (self.subs - 1)  
            
    def currentThick(self, context):
        if self.rimDepth + self.thick >= 5.80:
            self.thick = 5.8 - self.rimDepth
    
    wire : BoolProperty(name = "Wireframe", description = "Shows/Hides wireframe mode", default = True)
    arrayVis : BoolProperty(name = "Array Visibility", description = "Shows/Hides the Array Modifier", default = True)
    mirrorVis : BoolProperty(name = "Mirror Visibility", description = "Shows/Hides the Mirror Modifier", default = True)       
    arrayElements : IntProperty(name = "Pie Slices (Spokes)", description = "Splits the rim into a number of 'spokes' or 'pie slices'", default = 5, min = 2, max = 24)    
    subs : IntProperty(name = "Subdivisions", description = "Splits each individual 'spoke' or 'pie slice' into more slices", default = 12, min = 1, max = 48, update = currentSubs)
    spoke : IntProperty(name = "Spoke Size", description = "Enlarges spokes to help visualize rim elements", default = 8, min = 0,max = 46, update = currentSubs)
    rimDepth : FloatProperty(name = "Rim Depth", description = "Sets the depth of the rim at the outer edge", default = 2.0, min = 0.1, max = 4.0, update = currentThick)
    thick : FloatProperty(name = "Thickness", description = "Thickness of Rim Extrusion", default = 2.00, min = 0.5, max = 3.5, update = currentThick)    
    capSize : FloatProperty(name = "Center Cap Diameter", description = "Changes the size of the center cap", default = 3.0, min = 1.65, max = 7.0)
    capPro : FloatProperty(name = "Center Cap Thickness", description = "Gives the center cap a bit of protrusion", default = 1.0, min = 0.0, max = 6.0)       
    lugs : BoolProperty(name = "Lug Nuts", description = "Enable and Disable lug nuts", )
    lugsNum : IntProperty(name = "Lug Nuts", description = "Inserts Lug Nuts", default = 4, min = 3, max = 10)
    lugRot : FloatProperty(name = "Lugnut Rotation", description = "Rotates the lug nut individually to crate random tightening appearance", default = 0.0, min = 0.0, max = 59.0)
    lugSpin : FloatProperty(name = "Lugnut Spin Offset", description = "Offsets lug not rotation around the middle", default = 0.0, min = 0.0, max = 119.0)
    lugSpan : FloatProperty(name = "Lugnut Span", description = "Moves lug nuts closer together, or further apart", default = 3.8, min = 2.0, max = 12.0)
    
    #variables meant to be used 'globally'
    
    indexLocation : IntProperty(
        options = {'HIDDEN'},
        default = 0
    )
    
    #custom function to draw quad geometry

    
    def RimGeometryGenerator(self, spin, indexLocation, posX, posY, posZ, boolFaces, boolAppend, verts =[], faces =[]):        
        verts.append([ #index n
            posX,
            posY,
            posZ
        ])
         
        self.indexLocation = self.indexLocation +1           
        for index in range(self.subs):
            indexY = (index +1) *2
            indexZ = indexY +2
            verts.append([
                posX,
                math.sin(math.radians((spin/self.subs)*(index +1)))*posZ,
                math.cos(math.radians((spin/self.subs)*(index +1)))*posZ,            
            ])
            if boolAppend == True:
                self.indexLocation = self.indexLocation +1
                if boolFaces == True:
                    faces.append([((self.indexLocation - self.subs) -1),((self.indexLocation - self.subs) -2),(self.indexLocation -1),(self.indexLocation)])             
                if boolFaces == False and self.subs - self.spoke > index:
                    faces.append([((self.indexLocation - self.subs) -1),((self.indexLocation - self.subs) -2),(self.indexLocation -1),(self.indexLocation)]) 
            elif boolAppend == False:
                self.indexLocation = self.indexLocation +1
                   
    #custom function to assign materials to specific faces
    
    def MaterialAssignments(self, start, stop, matIndex):
        obj = bpy.context.object
        mesh = obj.data
        
        for i in range(start, stop):
            mesh.vertices[i].select = True

        bpy.ops.object.mode_set(mode = 'EDIT') 
        bpy.context.object.active_material_index = matIndex
        bpy.ops.object.material_slot_assign()
        bpy.ops.object.mode_set(mode = 'OBJECT')
        
        #self.DeselectAllFromObjectMode
        
        for polygon in bpy.context.active_object.data.polygons:
            polygon.select = False
        for edge in bpy.context.active_object.data.edges:
            edge.select = False
        for vertex in bpy.context.active_object.data.vertices:
            vertex.select = False        
            
    #custom function to smooth selected faces        
            
    def Smooth(self, start, stop):
        obj = bpy.context.object
        mesh = obj.data
        
        for i in range(start, stop):
            mesh.vertices[i].select = True

        bpy.ops.object.mode_set(mode = 'EDIT') 
        bpy.ops.mesh.faces_shade_smooth()
        bpy.ops.object.mode_set(mode = 'OBJECT')
        
        #self.DeselectAllFromObjectMode
        
        for polygon in bpy.context.active_object.data.polygons:
            polygon.select = False
        for edge in bpy.context.active_object.data.edges:
            edge.select = False
        for vertex in bpy.context.active_object.data.vertices:
            vertex.select = False
            
    #custom function to deselect all vertices of active mesh from object mode
        #function must be called in object mode        
    def DeselectAllFromObjectMode(self, context): 
        for polygon in bpy.context.active_object.data.polygons:
            polygon.select = False
        for edge in bpy.context.active_object.data.edges:
            edge.select = False
        for vertex in bpy.context.active_object.data.vertices:
            vertex.select = False
            
    
    #script begins
    
    def execute(self, context):
                
        #TODO - Create measurement conversions        
                
        #Variables
        
        sceneScale = bpy.data.scenes["Scene"].unit_settings.scale_length
        
        hubY = 0.0
        hubZ = .0588
        hubX = -.043
        hubXBack = .028
        rimX = -.04434
        rimXBack = .0129
        rimZ = .13     
        spin = 180 / (self.arrayElements)
        spinNut = 180 / (self.lugsNum)
        
        verts, edges, faces = [], [], []
        mat1Start = mat1End = mat2Start = mat2End = mat3Start = mat3End = mat4Start = mat4End = mat5Start = mat5End = smooth1Start = smooth1End = smooth2Start = Smooth2End = 0
        
        #material color variables
        
        mat1Color = (0.393, 0.393, 0.393, 1.0)
        mat2Color = (0.036, 0.036, 0.036, 1.0)
        mat3Color = (0.248, 0.393, 0.212, 1.0)
        mat4Color = (0.066, 0.109, 0.174, 1.0)
        mat5Color = (0.800, 0.408, 0.688, 1.0)
        
        #Material Variable assignments with checks, checks for materials already in the file with error checks, creates materials if missing
        
        try:
            mat1 = bpy.data.materials['Wheel_Primary']
        except KeyError:
            mat1 = bpy.data.materials.new(name = "Wheel_Primary")
            mat1.use_nodes = True
            nodes = mat1.node_tree.nodes
            bsdf = nodes.get("Principled BSDF")
            bsdf.inputs[0].default_value = mat1Color                       
            
        try:
            mat2 = bpy.data.materials['Wheel_Secondary']
        except KeyError:
            mat2 = bpy.data.materials.new(name = "Wheel_Secondary")
            mat2.use_nodes = True
            nodes = mat2.node_tree.nodes
            bsdf = nodes.get("Principled BSDF")
            bsdf.inputs[0].default_value = mat2Color
        try:
            mat3 = bpy.data.materials['Wheel_Misc1']
        except KeyError:
            mat3 = bpy.data.materials.new(name = "Wheel_Misc1")
            mat3.use_nodes = True
            nodes = mat3.node_tree.nodes
            bsdf = nodes.get("Principled BSDF")
            bsdf.inputs[0].default_value = mat3Color
        try:
            mat4 = bpy.data.materials['Wheel_Misc2']
        except KeyError:
            mat4 = bpy.data.materials.new(name = "Wheel_Misc2")
            mat4.use_nodes = True
            nodes = mat4.node_tree.nodes
            bsdf = nodes.get("Principled BSDF")
            bsdf.inputs[0].default_value = mat4Color
        try:
            mat5 = bpy.data.materials['Wheel_Nuts_Misc3']
        except KeyError:
            mat5 = bpy.data.materials.new(name = "Wheel_Nuts_Misc3")
            mat5.use_nodes = True
            nodes = mat5.node_tree.nodes
            bsdf = nodes.get("Principled BSDF")
            bsdf.inputs[0].default_value = mat5Color
            
        ########################################################################################
               
        #turn off auto-merge
        bpy.context.scene.tool_settings.use_mesh_automerge = False
        
        #Place first vertex and begin building the mesh

        #places vert index 0 at the center hub vert, this is fixed and unchanging.
        verts.append([ #index 0
            hubX - (self.capPro / 1000),
            0.0,
            0.0
        ])
        self.indexLocation = 0
        self.mat1Start = self.indexLocation
        
        ########################################################################################
        
        #builds initial triangular geometry
        
        verts.append([ #index 1
            hubX - (self.capPro / 1000),
            hubY,
            hubZ / self.capSize
        ])
        self.indexLocation = self.indexLocation +1

        for index in range(self.subs):
            indexY = index +1
            indexZ = indexY +1
            verts.append([
                hubX - (self.capPro / 1000),
                math.sin(math.radians((spin/self.subs)*(index +1)))*hubZ / self.capSize,
                math.cos(math.radians((spin/self.subs)*(index +1)))*hubZ / self.capSize,            
            ])
            self.indexLocation = self.indexLocation +1
            faces.append([0,indexY,indexZ])
                
                
        ########################################################################################
                
        #Quad Geometry function calls
        self.mat2Start = self.indexLocation + 1
        self.smooth1Start = 1
        self.RimGeometryGenerator(spin, self.indexLocation, (hubX + .0015), hubY, ((hubZ * 1.03) / self.capSize), True, True, verts, faces)
        self.mat1End = self.indexLocation + 1        
        self.smooth2Start = self.indexLocation + 1
        self.RimGeometryGenerator(spin, self.indexLocation, hubX, hubY, ((hubZ * 1.06) / self.capSize), True, True, verts, faces)
        self.smooth1End = self.indexLocation + 1
        #Line below draws the outer hub boundary, make sure it's fixed        
        self.RimGeometryGenerator(spin, self.indexLocation, hubX, hubY, hubZ, True, True, verts, faces)        
        self.RimGeometryGenerator(spin, self.indexLocation, (rimX + (self.rimDepth / 400)), hubY, (((rimZ - hubZ) * (1/3)) + hubZ), False, True, verts, faces)
        self.RimGeometryGenerator(spin, self.indexLocation, (rimX + (self.rimDepth / 200)), hubY, (((rimZ - hubZ) * (2/3)) + hubZ), False, True, verts, faces)
        self.mat3Start = self.indexLocation + 1        
        self.RimGeometryGenerator(spin, self.indexLocation, (rimX + (self.rimDepth / 100)), hubY, (rimZ - .008), False, True, verts, faces)
        self.mat2End = self.indexLocation + 1
        self.mat4Start = self.indexLocation + 1
        self.RimGeometryGenerator(spin, self.indexLocation, rimX, hubY, (rimZ - .008), True, True, verts, faces) 
        self.smooth2End = self.indexLocation + 1
        self.mat3End = self.indexLocation + 1        
        self.smooth3Start = self.indexLocation +1
        #Line below draws the outer rim boundary, make sure it's fixed        
        self.RimGeometryGenerator(spin, self.indexLocation, rimX, hubY, rimZ, True, True, verts, faces)
        #Line below draws the inner rim boundary, make sure it's fixed        
        self.RimGeometryGenerator(spin, self.indexLocation, rimXBack, hubY, rimZ, True, True, verts, faces)
        self.smooth3End = self.indexLocation +1
        self.mat4End = self.indexLocation + 1
        #Lines below draw the hub and select for material assignment
        self.mat5Start = self.indexLocation + 1
        self.RimGeometryGenerator(spin, self.indexLocation, (hubX + (self.thick / 100)), hubY, hubZ, True, False, verts, faces)
        self.RimGeometryGenerator(spin, self.indexLocation, hubX + .071045, hubY, hubZ, True, True, verts, faces)
        self.mat5End = self.indexLocation + 1
        
        ########################################################################################   
        
        #create collections
     
        collectionEmpty = bpy.context.blend_data.collections.new(name = 'Empties - Do Not Delete')
        bpy.context.collection.children.link(collectionEmpty)
        collection = bpy.context.blend_data.collections.new(name = 'Automation Rim Project')
        bpy.context.collection.children.link(collection)
        
        ########################################################################################
        
        #create the rim empty, put it in the empties collection and unlink data
        
        collectionEmpty.get("Empties - Do Not Delete")
        empty = bpy.ops.object.empty_add(type='PLAIN_AXES') 
        empty = bpy.context.active_object
        empty.rotation_euler[0] += math.radians(spin * 2)
        empty.name = "Rim Spinner - Do Not Delete"
        collectionEmpty.objects.link(empty)
        bpy.context.collection.objects.unlink(empty)        
        bpy.context.active_object.select_set(False)
        bpy.context.object.hide_set(True)
        
        #create the lug nut empty, put it in the empties collection and unlink data
        emptyNut = bpy.ops.object.empty_add(type='PLAIN_AXES') 
        emptyNut = bpy.context.active_object
        emptyNut.rotation_euler[0] += (math.radians(spinNut * 2) + (math.radians(self.lugSpin * - 1)))
        emptyNut.name = "Lug Nut Spinner - Do Not Delete"
        collectionEmpty.objects.link(emptyNut)
        bpy.context.collection.objects.unlink(emptyNut)        
        bpy.context.active_object.select_set(False)
        bpy.context.object.hide_set(True)
        
        ########################################################################################
        
        #create rim, assign materials, put it in rim colleciton
        
        name = "Automation Rim"
        mesh = bpy.data.meshes.new(name)
        obj = bpy.data.objects.new(name, mesh)
        col = bpy.data.collections.get("Automation Rim Project")
        col.objects.link(obj)
        bpy.context.view_layer.objects.active = obj
        mesh.from_pydata(verts, edges, faces)
        obj.data.materials.append(mat1)
        obj.data.materials.append(mat2)
        obj.data.materials.append(mat3)
        obj.data.materials.append(mat4)
        obj.data.materials.append(mat5)
        
        #sets edit mote to vertex select
        
        bpy.ops.object.mode_set(mode = 'EDIT') 
        bpy.ops.mesh.select_mode(type='VERT')
        bpy.ops.object.mode_set(mode = 'OBJECT')
        
        #Deselects all verts in mesh
        
        self.DeselectAllFromObjectMode
                
        #Material assignment to mesh function calls, plus changing viewport colors.
        
        self.MaterialAssignments(self.mat1Start, self.mat1End, 2)
        bpy.context.object.active_material.diffuse_color = mat3Color
        self.MaterialAssignments(self.mat2Start, self.mat2End, 0)
        bpy.context.object.active_material.diffuse_color = mat1Color
        self.MaterialAssignments(self.mat3Start, self.mat3End, 1)
        bpy.context.object.active_material.diffuse_color = mat2Color
        self.MaterialAssignments(self.mat4Start, self.mat4End, 3)
        bpy.context.object.active_material.diffuse_color = mat4Color
        self.MaterialAssignments(self.mat5Start, self.mat5End, 1)
        bpy.context.object.active_material.diffuse_color = mat2Color
        
        #Turn on auto-smooth and selectively smooth faces function call
        
        bpy.context.object.data.use_auto_smooth = True
        self.Smooth(self.smooth1Start, self.smooth1End)
        self.Smooth(self.smooth2Start, self.smooth2End)
        self.Smooth(self.smooth3Start, self.smooth3End)
        
        #Delte unneeded verts
        
        vertQuantity = 2 + (self.subs * 2)
        startVert = (5 + (self.subs * 4))
        endVert = (startVert + vertQuantity)
        secondVertStart = ((endVert - startVert) + 1) / 2 + startVert
        secondVertStart = int (secondVertStart)        
        startVertUpdate = secondVertStart - self.spoke        
        secondVertStartUpdate = endVert - self.spoke
            
        if self.subs > self.spoke:                   
            for i in range(startVertUpdate, secondVertStart):
                bpy.context.object.data.vertices[i].select = True
            for i in range(secondVertStartUpdate, endVert):
                bpy.context.object.data.vertices[i].select = True
            bpy.ops.object.mode_set(mode = 'EDIT')
            bpy.ops.mesh.delete(type='VERT')    
            bpy.ops.object.mode_set(mode = 'OBJECT')
        
        #Sharpen selected edges
        
        for i in range((startVert - (vertQuantity - (self.subs + 1))), (startVert-self.spoke)):
            bpy.context.object.data.vertices[i].select = True
        bpy.ops.object.mode_set(mode = 'EDIT')
        bpy.ops.mesh.mark_sharp()
        bpy.ops.object.mode_set(mode = 'OBJECT')
        
        for polygon in bpy.context.active_object.data.polygons:
            polygon.select = False
        for edge in bpy.context.active_object.data.edges:
            edge.select = False
        for vertex in bpy.context.active_object.data.vertices:
            vertex.select = False
            
        #Select and extrude rim
        if self.spoke > 0:
            pointA = startVert - vertQuantity + self.spoke - (self.subs * 2) - 2
            pointB = startVert + self.subs - self.spoke
            pointC = pointB + self.subs - self.spoke + 1
            pointD = pointC + self.subs - self.spoke + 1
            pointE = pointD + pointA
            
            for i in range((startVert - pointA), startVert):
                bpy.context.object.data.vertices[i].select = True  
            bpy.context.object.data.vertices[pointB].select = True 
            bpy.context.object.data.vertices[pointC].select = True
            for i in range(pointD, pointE):
                bpy.context.object.data.vertices[i].select = True        
        bpy.ops.object.mode_set(mode = 'EDIT')
        #extrude
        bpy.ops.mesh.extrude_region_move(TRANSFORM_OT_translate={"value":((self.thick / 100), 0, 0)})
        #selecting additional loop and adding material to extrusion
        bpy.ops.mesh.select_more()       
        bpy.context.object.active_material_index = 1
        bpy.ops.object.material_slot_assign()
        
        #cycling through object mode to deselect all verts
        bpy.ops.object.mode_set(mode = 'OBJECT')
        
        for polygon in bpy.context.active_object.data.polygons:
            polygon.select = False
        for edge in bpy.context.active_object.data.edges:
            edge.select = False
        for vertex in bpy.context.active_object.data.vertices:
            vertex.select = False
            
        #bpy.ops.object.mode_set(mode = 'EDIT')
        
        ########################################################################################
        
        #add modifiers
        
        #mirror modifier
        modMirror = obj.modifiers.new("Mirror", 'MIRROR')
        modMirror.use_axis[0] = False
        modMirror.use_axis[1] = True
        modMirror.merge_threshold = 0.00001
        modMirror.use_clip = False
        
        #array modifier        
        modArray = obj.modifiers.new("Array", 'ARRAY')
        modArray.count = self.arrayElements
        modArray.use_relative_offset = False
        modArray.use_object_offset = True
        modArray.offset_object = empty
        modArray.use_merge_vertices = True
        modArray.merge_threshold = 0.00001
        modArray.use_merge_vertices_cap = True
        
        #bevel modifier
        modBevel = obj.modifiers.new("Bevel", 'BEVEL')
        modBevel.width = 0.001
        modBevel.segments = 2
        modBevel.limit_method = 'WEIGHT'
        #TODO need to add driver to bevel modifier Amount
        
        #triangulate modifier
        modTri = obj.modifiers.new("Triangulate",'TRIANGULATE')
        modTri.show_viewport = False
        modTri.quad_method = 'FIXED'
        
        #Menu toggle visibility
        bpy.context.space_data.overlay.show_wireframes = self.wire
        modArray.show_viewport = self.arrayVis
        modMirror.show_viewport = self.mirrorVis
        
        ########################################################################################
            
        #Build Lug nut from empty cylinder primitive
        if self.lugs == True:
            nuts = bpy.ops.mesh.primitive_cylinder_add(
                vertices=6,
                depth=0.009, 
                radius=0.007, 
                enter_editmode=False, 
                align='WORLD', 
                location=(-0.047, 0, (self.lugSpan / 100)), 
                rotation=(0, 1.5708, 0), 
                scale=(1, 1, 1)
            )
            nuts = bpy.context.active_object
            nuts.name = "Lug Nuts"
            col.get("Automation Rim Project")
            col.objects.link(nuts)
            bpy.context.collection.objects.unlink(nuts)
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
            #rotates lug nuts with lugSpin variable to create a lugnut offset.
            bpy.ops.transform.rotate(value=(math.radians(self.lugSpin * - 1)), 
                orient_axis='X', 
                orient_type='GLOBAL', 
                orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), 
                orient_matrix_type='GLOBAL', 
                constraint_axis=(True, False, False), 
                mirror=True, 
                use_proportional_edit=False, 
                proportional_edit_falloff='SMOOTH', 
                proportional_size=0.00937039, 
                use_proportional_connected=False, 
                use_proportional_projected=False
            )
        
            #Deselect all verts, faces, edges.
            
            bpy.ops.object.mode_set(mode = 'EDIT')
            bpy.ops.mesh.faces_shade_smooth() 
            bpy.ops.mesh.select_mode(type='FACE')
            bpy.ops.object.mode_set(mode = 'OBJECT')
            
            for polygon in bpy.context.active_object.data.polygons:
                polygon.select = False
            for edge in bpy.context.active_object.data.edges:
                edge.select = False
            for vertex in bpy.context.active_object.data.vertices:
                vertex.select = False
            
            #self.DeselectAllFromObjectMode
            
            #Customize the mesh to become a lugnut
            
            nuts.data.polygons[4].select = True
            bpy.ops.object.mode_set(mode = 'EDIT')            
            bpy.ops.mesh.delete(type='FACE')
            bpy.ops.object.mode_set(mode = 'OBJECT')
            nuts.data.polygons[6].select = True
            bpy.ops.object.mode_set(mode = 'EDIT')
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
                MESH_OT_extrude_region={"use_normal_flip":False, 
                "use_dissolve_ortho_edges":False, 
                "mirror":False}, 
                TRANSFORM_OT_translate={"value":(0, 0, 0.00168543), 
                "orient_type":'NORMAL', 
                "orient_matrix":((2.36401e-06, 0.707107, 0.707106), (-2.19138e-06, 0.707106, -0.707107), (-1, 1.22077e-07, 3.22115e-06)), 
                "orient_matrix_type":'NORMAL', "constraint_axis":(False, False, True), 
                "mirror":False, 
                "use_proportional_edit":False, 
                "proportional_edit_falloff":'SMOOTH', 
                "proportional_size":0.00937039, 
                "use_proportional_connected":False, 
                "use_proportional_projected":False, 
                "snap":False, 
                "snap_target":'CLOSEST', 
                "snap_point":(0, 0, 0), 
                "snap_align":False, 
                "snap_normal":(0, 0, 0), 
                "gpencil_strokes":False, 
                "cursor_transform":False, 
                "texture_space":False, 
                "remove_on_cancel":False, 
                "release_confirm":False, 
                "use_accurate":False, 
                "use_automerge_and_split":False}
            )
            #bpy.ops.mesh.select_more()
            #bpy.ops.mesh.faces_shade_smooth()
            #bpy.ops.mesh.select_less()
            bpy.ops.mesh.extrude_region_move(
                MESH_OT_extrude_region={"use_normal_flip":False, 
                "use_dissolve_ortho_edges":False, 
                "mirror":False}, 
                TRANSFORM_OT_translate={"value":(0, 0, 0.00174559), 
                "orient_type":'NORMAL', 
                "orient_matrix":((2.10505e-06, 0.707107, 0.707106), (-2.45034e-06, 0.707106, -0.707107), (-1, -2.44153e-07, 3.22114e-06)), 
                "orient_matrix_type":'NORMAL', 
                "constraint_axis":(False, False, True), 
                "mirror":False, 
                "use_proportional_edit":False, 
                "proportional_edit_falloff":'SMOOTH', 
                "proportional_size":0.00937039, 
                "use_proportional_connected":False, 
                "use_proportional_projected":False, 
                "snap":False, 
                "snap_target":'CLOSEST', 
                "snap_point":(0, 0, 0), 
                "snap_align":False, 
                "snap_normal":(0, 0, 0), 
                "gpencil_strokes":False, 
                "cursor_transform":False, 
                "texture_space":False, 
                "remove_on_cancel":False, 
                "release_confirm":False, 
                "use_accurate":False, 
                "use_automerge_and_split":False}
            )
            bpy.ops.transform.resize(
                value=(1, 0.778713, 0.778713), 
                orient_type='GLOBAL', 
                orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), 
                orient_matrix_type='GLOBAL', 
                constraint_axis=(False, True, True), 
                mirror=True, 
                use_proportional_edit=False, 
                proportional_edit_falloff='SMOOTH', 
                proportional_size=0.00937039, 
                use_proportional_connected=False, 
                use_proportional_projected=False
            )
            bpy.ops.mesh.extrude_region_move(
                MESH_OT_extrude_region={"use_normal_flip":False, 
                "use_dissolve_ortho_edges":False, 
                "mirror":False}, 
                TRANSFORM_OT_translate={"value":(0, 0, 0.00151651), 
                "orient_type":'NORMAL', 
                "orient_matrix":((3.20965e-06, 0.707107, 0.707107), (-2.64024e-06, 0.707107, -0.707107), (-1, 4.02631e-07, 4.1365e-06)), 
                "orient_matrix_type":'NORMAL', 
                "constraint_axis":(False, False, True), 
                "mirror":False, 
                "use_proportional_edit":False, 
                "proportional_edit_falloff":'SMOOTH', 
                "proportional_size":0.00937039, 
                "use_proportional_connected":False, 
                "use_proportional_projected":False, 
                "snap":False, "snap_target":'CLOSEST', 
                "snap_point":(0, 0, 0), 
                "snap_align":False, 
                "snap_normal":(0, 0, 0), 
                "gpencil_strokes":False, 
                "cursor_transform":False, 
                "texture_space":False, 
                "remove_on_cancel":False, 
                "release_confirm":False, 
                "use_accurate":False, 
                "use_automerge_and_split":False}
            )
            bpy.ops.transform.resize(
                value=(1, 0.425487, 0.425487), 
                orient_type='GLOBAL', 
                orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), 
                orient_matrix_type='GLOBAL', 
                constraint_axis=(False, True, True), 
                mirror=True, 
                use_proportional_edit=False, 
                proportional_edit_falloff='SMOOTH', 
                proportional_size=0.00937039, 
                use_proportional_connected=False, 
                use_proportional_projected=False
            )
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.transform.rotate(value=(math.radians(self.lugRot)), 
                orient_axis='X', 
                orient_type='GLOBAL', 
                orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), 
                orient_matrix_type='GLOBAL', 
                constraint_axis=(True, False, False), 
                mirror=True, 
                use_proportional_edit=False, 
                proportional_edit_falloff='SMOOTH', 
                proportional_size=0.00937039, 
                use_proportional_connected=False, 
                use_proportional_projected=False
            )            
            bpy.ops.object.mode_set(mode = 'OBJECT')
            
            ###########################################################################################
            
            #Add Modifiers
            
            #bevel modifier
            nutBevel = nuts.modifiers.new("Bevel", 'BEVEL')
            nutBevel.width = 0.0004
            nutBevel.segments = 2
            nutBevel.limit_method = 'ANGLE'
            nutBevel.angle_limit = 0.785398
            
            #array modifier
            nutArray = nuts.modifiers.new("Array", 'ARRAY')
            nutArray.count = self.lugsNum
            nutArray.use_relative_offset = False
            nutArray.use_object_offset = True
            nutArray.offset_object = emptyNut
            nutArray.use_merge_vertices = True
            nutArray.merge_threshold = 0.00001
            nutArray.use_merge_vertices_cap = True
            

        elif self.lugs == False:
            print("lug nuts off")
        
        ########################################################################################
                    
        return {'FINISHED'}

def register():
    bpy.utils.register_class(CreateRim)
    bpy.utils.register_class(AddRim)


def unregister():
    bpy.utils.unregister_class(CreateRim)
    bpy.utils.unregister_class(AddRim)



    
        #bpy.ops.object.material_slot_add()