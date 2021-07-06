# SimpleDataFlow (not ready yet)
A simple tool used to analyze data flow.

| [Minimal Example](#minimal-example) - [Data Sets](#data-sets) - [Tools](#custom-tools) - [Modifiers](#custom-modifiers) - [Inspectors](#custom-inspectors) - [Static Attributes](#static-attributes) |
|-|

![](https://github.com/hoffstadt/SimpleDataFlow/blob/main/example.PNG)

## Minimal Example
Although not very useful, below is the minimal code required to start:
```python
import simple_data_flow as sdf

app = sdf.App()
app.start()
```

## Basics
A _Simple Data Flow_ application consists of a few components, namely:
1. **Data Graph** - the center region that contains nodes
2. **Data sets** - data of any form that can be dropped onto the data graph
3. **Modifiers** - components that take in data and performs operation on it, outputting another data set.
4. **Inspectors** - components that take in data and takes measurements but does not affect the data set.
5. **Tools** - similar to **Inspectors** but these components do not have an output.

## Data Sets
Data sets are the roots in node graph. The data itself can be any form. Below is a simple example of adding data sets:

```python
import simple_data_flow as sdf

app = sdf.App()

app.add_data_set("New Data", [-5.0, -5.0, -3.0, -3.0, 0.0, 0.0, 3.0, 3.0, 5.0, 5.0])

app.start()
```

## Custom Tools
Creating a new tool requires the developer to create a new class derived from `Node`. It is the developers responsibility to create a factory static method and override the `execute` method. The constructor will add however many input attributes are required to perform its operation. Most tools will also need to add a [static attribute](#static-attributes). The typical steps involved within the `execute` method are as follows:
1. Retrieve data from input attributes.
2. Retrieve data from static attributes.
3. Perform operations.
4. Set some values in the static attributes.
5. Call `finish`.


Below is a simple tool that displays the length of the incoming data:
```python
import simple_data_flow as sdf
from simple_data_flow import dpg


class NewAttribute(sdf.StaticNodeAttribute):

    def __init__(self):
        super().__init__()
        self.custom_id = dpg.generate_uuid()

    def submit(self, parent):

        with dpg.node_attribute(parent=parent, attribute_type=dpg.mvNode_Attr_Static,
                                user_data=self, id=self._uuid):
            dpg.add_input_int(label="Length", width=150, id=self.custom_id, readonly=True, step=0)


class NewNode(sdf.Node):

    @staticmethod
    def factory(name, data):
        node = NewNode(name, data)
        return node

    def __init__(self, label: str, data):
        super().__init__(label, data)

        # add input attributes
        self.add_input_attribute(sdf.InputNodeAttribute("input"))
        
        # add custom static attributes
        self.add_static_attribute(NewAttribute())

    def execute(self):

        # input data
        input_data_1 = self._input_attributes[0].get_data()

        # static attribute IDs
        custom_id = self._static_attributes[0].custom_id

        # perform operations
        result = len(input_data_1)

        # set values
        dpg.set_value(custom_id, result)

        # call finish
        self.finish()


app = sdf.App()

app.add_tool("New Tool", NewNode.factory)

app.start()

```

## Custom Modifiers
Creating a new modifier requires the developer to create a new class derived from `Node`. It is the developers responsibility to create a factory static method and override the `execute` method. The constructor will add however many input attributes are required to perform its operation. The constructor will also add the required number of output attributes. Most tools will also need to add a [static attribute](#static-attributes). The typical steps involved within the `execute` method are as follows:
1. Retrieve data from input attributes.
2. Retrieve data from static attributes.
3. Perform operations.
4. Call `execute` method of each output attribute, passing in output data.
5. Call `finish`.

Below is a simple example of a modifier that subtracts some value from each value in the data set:
```python
import simple_data_flow as sdf
from simple_data_flow import dpg


class NewAttribute(sdf.StaticNodeAttribute):

    def __init__(self):
        super().__init__()
        self.custom_id = dpg.generate_uuid()

    def submit(self, parent):

        with dpg.node_attribute(parent=parent, attribute_type=dpg.mvNode_Attr_Static,
                                user_data=self, id=self._uuid):
            dpg.add_input_int(label="Subtract Value", width=150, id=self.custom_id, step=0)


class NewNode(sdf.Node):

    @staticmethod
    def factory(name, data):
        node = NewNode(name, data)
        return node

    def __init__(self, label: str, data):
        super().__init__(label, data)

        # add input attributes
        self.add_input_attribute(sdf.InputNodeAttribute("input"))

        # add custom static attributes
        self.add_static_attribute(NewAttribute())

        # add output attributes
        self.add_output_attribute(sdf.OutputNodeAttribute("output"))

    def execute(self):

        # input data
        input_data_1 = self._input_attributes[0].get_data()

        # static attribute value
        custom_id = self._static_attributes[0].custom_id
        subtract_value = dpg.get_value(custom_id)

        # perform operations
        new_data = []
        for value in input_data_1:
            new_data.append(value - subtract_value)

        # call execute on output attributes with data
        self._output_attributes[0].execute(new_data)

        # call finish
        self.finish()


app = sdf.App()

app.add_modifier("New Modifier", NewNode.factory)

app.start()

```

## Custom Inspectors
Creating a new inspector requires the developer to create a new class derived from `Node`. It is the developers responsibility to create a factory static method and override the `execute` method. The constructor will add however many input attributes are required to perform its operation. The constructor will also add the required number of output attributes. Most tools will also need to add a [static attribute](#static-attributes). The typical steps involved within the `execute` method are as follows:
1. Retrieve data from input attributes.
2. Retrieve data from static attributes.
3. Perform operations.
4. Call `execute` method of each output attribute, passing in output data.
5. Call `finish`.

Below is a simple example of an inspector that finds the maximum value of a data set:
```python
import simple_data_flow as sdf
from simple_data_flow import dpg

class NewNode(sdf.Node):

    @staticmethod
    def factory(name, data):
        node = NewNode(name, data)
        return node

    def __init__(self, label: str, data):
        super().__init__(label, data)

        # add input attributes
        self.add_input_attribute(sdf.InputNodeAttribute("input"))

        # add output attributes
        self.add_output_attribute(sdf.OutputNodeAttribute("output"))

    def execute(self):

        # input data
        input_data_1 = self._input_attributes[0].get_data()

        # perform operations
        max_value = input_data_1[0]
        for value in input_data_1:
            if value > max_value:
                max_value = value

        # call execute on output attributes with data
        self._output_attributes[0].execute(max_value)

        # call finish
        self.finish()


app = sdf.App()

app.add_inspector("New Inspector", NewNode.factory)

app.start()

```

## Static Attributes
Inspectors, Modifiers, Tools, and Data Sets are all nodes. Nodes are composed of input, output, and static attributes. Input and output nodes are just simple values in which you can override the label. Static attributes 
To add a new static attribute, the developer must create a new class derived from `StaticNodeAttribute`. This new class must override the `submit` method. See a simple example below:

```python
class NewAttribute(sdf.StaticNodeAttribute):

    def __init__(self):
        super().__init__()
        self.custom_id = dpg.generate_uuid()

    def submit(self, parent):

        with dpg.node_attribute(parent=parent, attribute_type=dpg.mvNode_Attr_Static,
                                user_data=self, id=self._uuid):
            dpg.add_input_int(label="Length", width=150, id=self.custom_id, readonly=True, step=0)
```
