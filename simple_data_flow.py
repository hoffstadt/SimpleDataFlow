import dearpygui.dearpygui as dpg

########################################################################################################################
# Simple Data Flow
########################################################################################################################
# Table of Contents
#
#   0 Themes
#   1 Node DPG Wrappings
#   2 Drag & Drop
#   3 Inspectors
#   4 Modifiers
#   5 Tools
#   6 Application
#
# How do I use this tool? (check the bottom of this file)
#   0. Create an App Instance. (app = App())
#   1. Add data sets.          (add_data_set method)
#   2. Add modifiers.          (add_modifier method)
#   3. Add inspectors.         (add_inspector method)
#   4. Add tools.              (add_tool method)
#   5. Start App.              (start method)
#
# How do I create a Modifier/Inspector/Tool? (check the MinMaxNode below)
#   0. Create a class derived from "Node". (Call it "NewNode" for this example)
#   1. In the constructor, add attributes.
#   2. Override the "execute" method that does the following:
#     a. First argument is "data".
#     b. Retrieve input attribute data.
#     c. Perform your operations.
#     d. Call "execute" methods of your output attributes (modifiers).
#     e. Call "finish".
#   3. Create a static method called "factory" that creates a returns a "NewNode".
#   4. Call either add_tool, add_modifier, or add_inspector method of app like so:
#     a. "app.add_modifier("NewNode", NewNode.factory, None)"
#     b. The 3rd argument of DragSource can be any data and will be passed into the factory's second argument
########################################################################################################################

########################################################################################################################
# Themes
########################################################################################################################

with dpg.theme() as _source_theme:
    dpg.add_theme_color(dpg.mvThemeCol_Button, [25, 119, 0])
    dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, [25, 255, 0])
    dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, [25, 119, 0])

with dpg.theme() as _completion_theme:
    dpg.add_theme_color(dpg.mvNodeCol_TitleBar, [37, 28, 138], category=dpg.mvThemeCat_Nodes)
    dpg.add_theme_color(dpg.mvNodeCol_TitleBarHovered, [37, 28, 138], category=dpg.mvThemeCat_Nodes)
    dpg.add_theme_color(dpg.mvNodeCol_TitleBarSelected, [37, 28, 138], category=dpg.mvThemeCat_Nodes)


########################################################################################################################
# Node DPG Wrappings
########################################################################################################################
class StaticNodeAttribute:

    def __init__(self):
        self._uuid = dpg.generate_uuid()

    def begin(self):
        dpg.push_container_stack(self._uuid)

    def end(self):
        dpg.pop_container_stack()

    def submit(self, parent):
        dpg.add_node_attribute(parent=parent, attribute_type=dpg.mvNode_Attr_Static, user_data=self, id=self._uuid)


class OutputNodeAttribute:

    def __init__(self, label: str = "output"):

        self._label = label
        self.uuid = dpg.generate_uuid()
        self._children = []  # output attributes
        self._data = None

    def add_child(self, parent, child):

        dpg.add_node_link(self.uuid, child.uuid, parent=parent)
        child.set_parent(self)
        self._children.append(child)

    def execute(self, data):
        self._data = data
        for child in self._children:
            child._data = self._data

    def submit(self, parent):

        with dpg.node_attribute(parent=parent, attribute_type=dpg.mvNode_Attr_Output,
                                user_data=self, id=self.uuid):
            dpg.add_text(self._label)


class InputNodeAttribute:

    def __init__(self, label: str = "input"):

        self._label = label
        self.uuid = dpg.generate_uuid()
        self._parent = None  # input attribute
        self._data = None

    def get_data(self):
        return self._data

    def set_parent(self, parent: OutputNodeAttribute):
        self._parent = parent

    def submit(self, parent):

        with dpg.node_attribute(parent=parent, user_data=self, id=self.uuid):
            dpg.add_text(self._label)


class Node:

    def __init__(self, label: str, data):

        self.label = label
        self.uuid = dpg.generate_uuid()
        self._input_attributes = []
        self._static_attributes = []
        self._output_attributes = []
        self._data = data

    def finish(self):
        dpg.set_item_theme(self.uuid, _completion_theme)

    def add_input_attribute(self, attribute: InputNodeAttribute):
        self._input_attributes.append(attribute)

    def add_output_attribute(self, attribute: OutputNodeAttribute):
        self._output_attributes.append(attribute)

    def add_static_attribute(self, attribute: StaticNodeAttribute):
        self._static_attributes.append(attribute)

    def execute(self):

        for attribute in self._output_attributes:
            attribute.execute(self._data)

        self.finish()

    def submit(self, parent):

        with dpg.node(parent=parent, label=self.label, id=self.uuid):

            with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Static):
                dpg.add_button(label="Execute", user_data=self, callback=lambda s, a, u: u.execute())

            for attribute in self._input_attributes:
                attribute.submit(self.uuid)

            for attribute in self._static_attributes:
                attribute.submit(self.uuid)

            for attribute in self._output_attributes:
                attribute.submit(self.uuid)


class NodeEditor:

    @staticmethod
    def _link_callback(sender, app_data, user_data):
        output_attr_uuid, input_attr_uuid = app_data

        input_attr = dpg.get_item_user_data(input_attr_uuid)
        output_attr = dpg.get_item_user_data(output_attr_uuid)

        output_attr.add_child(sender, input_attr)

    def __init__(self):

        self._nodes = []
        self.uuid = dpg.generate_uuid()

    def add_node(self, node: Node):
        self._nodes.append(node)

    def on_drop(self, sender, app_data, user_data):

        source, generator, data = app_data
        node = generator(source.label, data)
        node.submit(self.uuid)
        self.add_node(node)

    def submit(self, parent):

        with dpg.node_editor(parent=parent, id=self.uuid, user_data=self, callback=NodeEditor._link_callback,
                             width=-160, height=-1, drop_callback=lambda s, a, u: dpg.get_item_user_data(s).on_drop(s, a, u)):

            for node in self._nodes:
                node.submit(self.uuid)


########################################################################################################################
# Drag & Drop
########################################################################################################################
class DragSource:

    def __init__(self, label: str, node_generator, data):

        self.label = label
        self._generator = node_generator
        self._data = data

    def submit(self, parent):

        dpg.add_button(label=self.label, parent=parent)
        dpg.set_item_theme(dpg.last_item(), _source_theme)

        with dpg.drag_payload(parent=dpg.last_item(), drag_data=(self, self._generator, self._data)):
            dpg.add_text(f"Name: {self.label}")


class DragSourceContainer:

    def __init__(self, label: str, width: int = 150, height: int = -1):

        self._label = label
        self._width = width
        self._height = height
        self._uuid = dpg.generate_uuid()
        self._children = []  # drag sources

    def add_drag_source(self, source: DragSource):

        self._children.append(source)

    def submit(self, parent):

        with dpg.child(parent=parent, width=self._width, height=self._height, id=self._uuid, menubar=True) as child_parent:
            with dpg.menu_bar():
                dpg.add_menu(label=self._label)

            for child in self._children:
                child.submit(child_parent)


########################################################################################################################
# Inspectors
########################################################################################################################
class MaxMinAttribute(StaticNodeAttribute):

    def __init__(self):
        super().__init__()
        self.min_id = dpg.generate_uuid()
        self.max_id = dpg.generate_uuid()

    def submit(self, parent):

        with dpg.node_attribute(parent=parent, attribute_type=dpg.mvNode_Attr_Static,
                                user_data=self, id=self._uuid):
            with dpg.group(width=150):
                dpg.add_text("Not Calculated", label="Min", show_label=True, id=self.min_id)
                dpg.add_text("Not Calculated", label="Max", show_label=True, id=self.max_id)


class MaxMinNode(Node):

    @staticmethod
    def factory(name, data):
        node = MaxMinNode(name, data)
        return node

    def __init__(self, label: str, data):
        super().__init__(label, data)

        self.add_input_attribute(InputNodeAttribute("values"))
        self.add_static_attribute(MaxMinAttribute())
        self.add_output_attribute(OutputNodeAttribute("min"))
        self.add_output_attribute(OutputNodeAttribute("max"))

    def execute(self):

        # get input attribute data
        values = self._input_attributes[0].get_data()

        # perform actual operations
        min_value = values[0]
        max_value = values[0]

        for i in range(0, len(values)):

            if values[i] > max_value:
                max_value = values[i]

            if values[i] < min_value:
                min_value = values[i]

        dpg.set_value(self._static_attributes[0].min_id, str(min_value))
        dpg.set_value(self._static_attributes[0].max_id, str(max_value))

        # execute output attributes
        self._output_attributes[0].execute(min_value)
        self._output_attributes[1].execute(max_value)

        self.finish()


########################################################################################################################
# Modifiers
########################################################################################################################
class DataShiftAttribute(StaticNodeAttribute):

    def __init__(self):
        super().__init__()
        self.x_shift = dpg.generate_uuid()
        self.y_shift = dpg.generate_uuid()

    def submit(self, parent):

        with dpg.node_attribute(parent=parent, attribute_type=dpg.mvNode_Attr_Static,
                                user_data=self, id=self._uuid):
            dpg.add_input_int(label="x", id=self.x_shift, step=0, width=150)
            dpg.add_input_int(label="y", id=self.y_shift, step=0, width=150)


class DataShifterNode(Node):

    @staticmethod
    def factory(name, data):
        node = DataShifterNode(name, data)
        return node

    def __init__(self, label: str, data):
        super().__init__(label, data)

        self.add_input_attribute(InputNodeAttribute("x"))
        self.add_input_attribute(InputNodeAttribute("y"))
        self.add_static_attribute(DataShiftAttribute())
        self.add_output_attribute(OutputNodeAttribute("x mod"))
        self.add_output_attribute(OutputNodeAttribute("y mod"))

    def execute(self):

        # get values from static attributes
        x_shift = dpg.get_value(self._static_attributes[0].x_shift)
        y_shift = dpg.get_value(self._static_attributes[0].y_shift)

        # get input attribute data
        x_orig_data = self._input_attributes[0].get_data()
        y_orig_data = self._input_attributes[1].get_data()

        # perform actual operations
        x_data = []
        for i in range(0, len(x_orig_data)):
            x_data.append(x_orig_data[i] + x_shift)

        y_data = []
        for i in range(0, len(y_orig_data)):
            y_data.append(y_orig_data[i] + y_shift)

        # execute output attributes
        self._output_attributes[0].execute(x_data)
        self._output_attributes[1].execute(y_data)

        self.finish()


########################################################################################################################
# Tools
########################################################################################################################
class ViewNodeAttribute_1D(StaticNodeAttribute):

    def __init__(self):
        super().__init__()
        self.simple_plot = dpg.generate_uuid()

    def submit(self, parent):

        with dpg.node_attribute(parent=parent, attribute_type=dpg.mvNode_Attr_Static,
                                user_data=self, id=self._uuid):
            dpg.add_simple_plot(label="Data View", width=200, height=80, id=self.simple_plot)


class ViewNode_1D(Node):

    @staticmethod
    def factory(name, data):
        node = ViewNode_1D(name, data)
        return node

    def __init__(self, label: str, data):
        super().__init__(label, data)

        self.add_input_attribute(InputNodeAttribute())
        self.add_static_attribute(ViewNodeAttribute_1D())

    def execute(self):

        plot_id = self._static_attributes[0].simple_plot
        dpg.set_value(plot_id, self._input_attributes[0].get_data())
        self.finish()


class ViewNodeAttribute_2D(StaticNodeAttribute):

    def __init__(self):
        super().__init__()
        self.x_axis = dpg.generate_uuid()
        self.y_axis = dpg.generate_uuid()

    def submit(self, parent):

        with dpg.node_attribute(parent=parent, attribute_type=dpg.mvNode_Attr_Static,
                                user_data=self, id=self._uuid):

            with dpg.plot(height=400, width=400, no_title=True):
                dpg.add_plot_axis(dpg.mvXAxis, label="", id=self.x_axis)
                dpg.add_plot_axis(dpg.mvYAxis, label="", id=self.y_axis)


class ViewNode_2D(Node):

    @staticmethod
    def factory(name, data):
        node = ViewNode_2D(name, data)
        return node

    def __init__(self, label: str, data):
        super().__init__(label, data)

        self.add_input_attribute(InputNodeAttribute("x"))
        self.add_input_attribute(InputNodeAttribute("y"))
        self.add_static_attribute(ViewNodeAttribute_2D())

    def execute(self):

        x_axis_id = self._static_attributes[0].x_axis
        y_axis_id = self._static_attributes[0].y_axis

        x_orig_data = self._input_attributes[0].get_data()
        y_orig_data = self._input_attributes[1].get_data()

        dpg.add_line_series(x_orig_data, y_orig_data, parent=y_axis_id)
        dpg.fit_axis_data(x_axis_id)
        dpg.fit_axis_data(y_axis_id)

        self.finish()


########################################################################################################################
# Application
########################################################################################################################
class App:

    @staticmethod
    def data_node_factory(name, data):
        node = Node(name, data)
        node.add_output_attribute(OutputNodeAttribute("data"))
        return node

    def __init__(self):

        self.data_set_container = DragSourceContainer("Data Sets", 150, -500)
        self.tool_container = DragSourceContainer("Tools", 150, -1)
        self.inspector_container = DragSourceContainer("Inspectors", 150, -500)
        self.modifier_container = DragSourceContainer("Modifiers", 150, -1)

        self.add_data_set("Test Data", [-5.0, -5.0, -3.0, -3.0, 0.0, 0.0, 3.0, 3.0, 5.0, 5.0])
        self.add_tool("1D Data View", ViewNode_1D.factory)
        self.add_tool("2D Data View", ViewNode_2D.factory)
        self.add_inspector("MinMax", MaxMinNode.factory)
        self.add_modifier("Data Shifter", DataShifterNode.factory)

    def add_data_set(self, label, data):
        self.data_set_container.add_drag_source(DragSource(label, App.data_node_factory, data))

    def add_tool(self, label, factory, data=None):
        self.tool_container.add_drag_source(DragSource(label, factory, data))

    def add_inspector(self, label, factory, data=None):
        self.inspector_container.add_drag_source(DragSource(label, factory, data))

    def add_modifier(self, label, factory, data=None):
        self.modifier_container.add_drag_source(DragSource(label, factory, data))

    def start(self):

        dpg.setup_registries()
        dpg.setup_viewport()
        dpg.set_viewport_title("Simple Data Flow")
        node_editor = NodeEditor()

        with dpg.window() as main_window:

            with dpg.menu_bar():

                with dpg.menu(label="Operations"):

                    dpg.add_menu_item(label="Reset", callback=lambda:dpg.delete_item(node_editor.uuid, children_only=True))

            with dpg.group(horizontal=True) as group:

                # left panel
                with dpg.group() as left_panel:
                    self.data_set_container.submit(left_panel)
                    self.modifier_container.submit(left_panel)

                # center panel
                node_editor.submit(group)

                # right panel
                with dpg.group() as right_panel:
                    self.inspector_container.submit(right_panel)
                    self.tool_container.submit(right_panel)

        dpg.set_primary_window(main_window, True)
        dpg.start_dearpygui()


if __name__ == "__main__":

    app = App()
    app.start()
