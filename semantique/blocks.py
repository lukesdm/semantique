__all__ = [
  "concept",
  "entity",
  "event",
  "resource",
  "appearance",
  "artifacts",
  "atmosphere",
  "reflectance",
  "topography",
  "result",
  "self",
  "collection",
  "value_label",
  "geometries",
  "time_instant",
  "time_interval",
  "CubeProxy",
  "CubeCollectionProxy"
]

from semantique.extent import SpatialExtent, TemporalExtent

def _parse_filter_expression(*args):
  n_args = len(args)
  if n_args == 2:
    component = None
    operator = args[0]
    y = args[1]
  elif n_args == 3:
    component = args[0]
    operator = args[1]
    y = args[2]
  else:
    raise ValueError(
      f"Filter expression should be of length 3 (component, operator, y) "
      f"or 2 (operator, y), not {n_args}"
    )
  return component, operator, y

class CubeProxy(dict):
  """Proxy object of a data cube.

  This proxy object serves as a substitute for a real data cube object. All
  data cube specific actions (i.e. *verbs*) can be called as methods of this
  object. However, the proxy object iself does not contain any data, and the
  actions will not be applied. Instead, a textual recipe is constructed which
  will be executed only at the stage of query processing.

  Parameters
  ----------
    obj : :obj:`dict`
      Textual reference that can be solved by the query
      processor. Normally not constructed by hand, but obtained by calling one
      of the dedicated reference functions or by applying verbs to existing
      CubeProxy or CubeCollectionProxy objects.

  """

  def __init__(self, obj):
    super(CubeProxy, self).__init__(obj)

  def _append_verb(self, name, collector = False, **kwargs):
    verb = {"type": "verb", "name": name, "params": kwargs}
    if "do" in self:
      self["do"].append(verb)
      return CubeCollectionProxy(self) if collector else self
    else:
      new = {"type": "processing_chain", "with": self, "do": [verb]}
      return CubeCollectionProxy(new) if collector else CubeProxy(new)

  def evaluate(self, operator, y = None, **kwargs):
    """Evaluate an expression for each pixel in a data cube.

    """
    if y is None:
      kwargs.update({"operator": operator})
    else:
      kwargs.update({"operator": operator, "y": y})
    return self._append_verb("evaluate", **kwargs)

  def extract(self, dimension, component = None, **kwargs):
    """Extract coordinates labels of a dimension as a new data cube.

    """
    if component is None:
      kwargs.update({"dimension": dimension})
    else:
      kwargs.update({"dimension": dimension, "component": component})
    return self._append_verb("extract", **kwargs)

  def filter(self, filterer, **kwargs):
    """Filter the values in a data cube.

    """
    kwargs.update({"filterer": filterer})
    return self._append_verb("filter", **kwargs)

  def filter_time(self, *filterer, **kwargs):
    """Filter a data cube along the temporal dimension.

    """
    component, operator, y = _parse_filter_expression(*filterer)
    eval_obj = CubeProxy({"type": "self"})
    filterer = eval_obj.extract("time", component).evaluate(operator, y)
    kwargs.update({"filterer": filterer})
    return self._append_verb("filter", **kwargs)

  def filter_space(self, *filterer, **kwargs):
    """Filter a data cube along the spatial dimension.

    """
    component, operator, y = _parse_filter_expression(*filterer)
    eval_obj = CubeProxy({"type": "self"})
    filterer = eval_obj.extract("space", component).evaluate(operator, y)
    kwargs.update({"filterer": filterer})
    return self._append_verb("filter", **kwargs)

  def groupby(self, grouper, **kwargs):
    """Group the values in a data cube.

    """
    kwargs.update({"grouper": grouper})
    return self._append_verb("groupby", collector = True, **kwargs)

  def groupby_time(self, component = None, **kwargs):
    """Group a data cube along the temporal dimension.

    """
    eval_obj = CubeProxy({"type": "self"})
    if isinstance(component, list):
      comps = [eval_obj.extract("time", x) for x in component]
      grouper = CubeCollectionProxy({"type": "collection", "elements": comps})
    else:
      grouper = eval_obj.extract("time", component)
    kwargs.update({"grouper": grouper})
    return self._append_verb("groupby", collector = True, **kwargs)

  def groupby_space(self, component = None, **kwargs):
    """Group a data cube along the spatial dimension.

    """
    eval_obj = CubeProxy({"type": "self"})
    if isinstance(component, list):
      comps = [eval_obj.extract("space", x) for x in component]
      grouper = CubeCollectionProxy({"type": "collection", "elements": comps})
    else:
      grouper = eval_obj.extract("space", component)
    kwargs.update({"grouper": grouper})
    return self._append_verb("groupby", collector = True, **kwargs)

  def label(self, label, **kwargs):
    """Attach a label to a data cube.

    """
    kwargs.update({"label": label})
    return self._append_verb("label", **kwargs)

  def reduce(self, dimension, reducer, **kwargs):
    """Reduce the dimensionality of a data cube.

    """
    kwargs.update({"dimension": dimension, "reducer": reducer})
    return self._append_verb("reduce", **kwargs)

class CubeCollectionProxy(dict):
  """Proxy object of a data cube collection.

  This proxy object serves as a substitute for a collecton of real data cube
  objects. All data cube collection specific actions (i.e. *verbs*) can be
  called as methods of this object. However, the proxy object iself does not
  contain any data, and the actions will not be applied. Instead, a textual
  recipe is constructed which will be executed only at the stage of query
  processing.

  Parameters
  ----------
    obj : :obj:`dict`
      Textual reference that can be solved by the query
      processor. Normally not constructed by hand, but obtained by calling one
      of the dedicated reference functions or by applying verbs to existing
      CubeProxy or CubeCollectionProxy objects.

  """

  def __init__(self, obj):
    super(CubeCollectionProxy, self).__init__(obj)

  def _append_verb(self, name, combiner = False, **kwargs):
    verb = {"type": "verb", "name": name, "params": kwargs}
    if "do" in self:
      self["do"].append(verb)
      return CubeProxy(self) if combiner else self
    else:
      new = {"type": "processing_chain", "with": self, "do": [verb]}
      return CubeProxy(new) if combiner else CubeCollectionProxy(new)

  def compose(self, **kwargs):
    """Create a categorical composition from multiple data cubes.

    """
    return self._append_verb("compose", combiner = True)

  def concatenate(self, dimension, **kwargs):
    """Concatenate multiple data cubes along a new or existing dimension.

    """
    kwargs.update({"dimension": dimension})
    return self._append_verb("concatenate", combiner = True, **kwargs)

  def merge(self, reducer, **kwargs):
    """Merge values of multiple data cubes into a single value per pixel.

    """
    kwargs.update({"reducer": reducer})
    return self._append_verb("merge", combiner = True, **kwargs)

  def evaluate(self, operator, y = None, **kwargs):
    """Apply the evaluate verb to each data cube in a collection.

    """
    if y is None:
      kwargs.update({"operator": operator})
    else:
      kwargs.update({"operator": operator, "y": y})
    return self._append_verb("evaluate", **kwargs)

  def extract(self, dimension, component = None, **kwargs):
    """Apply the extract verb to each data cube in a collection.

    """
    if component is None:
      kwargs.update({"dimension": dimension})
    else:
      kwargs.update({"dimension": dimension, "component": component})
    return self._append_verb("extract", **kwargs)

  def filter(self, filterer, **kwargs):
    """Apply the filter verb to each data cube in a collection.

    """
    kwargs.update({"filterer": filterer})
    return self._append_verb("filter", **kwargs)

  def filter_time(self, *filterer, **kwargs):
    """Apply the filter_time verb to each data cube in a collection.

    """
    component, operator, y = _parse_filter_expression(*filterer)
    eval_obj = CubeProxy({"type": "self"})
    filterer = eval_obj.extract("time", component).evaluate(operator, y)
    kwargs.update({"filterer": filterer})
    return self._append_verb("filter", **kwargs)

  def filter_space(self, *filterer, **kwargs):
    """Apply the filter_space verb to each data cube in a collection.

    """
    component, operator, y = _parse_filter_expression(*filterer)
    eval_obj = CubeProxy({"type": "self"})
    filterer = eval_obj.extract("space", component).evaluate(operator, y)
    kwargs.update({"filterer": filterer})
    return self._append_verb("filter", **kwargs)

  def label(self, label, **kwargs):
    """Apply the label verb to each data cube in a collection.

    """
    kwargs.update({"label": label})
    return self._append_verb("label", **kwargs)

  def reduce(self, dimension, reducer, **kwargs):
    """Apply the reduce verb to each data cube in a collection.

    """
    kwargs.update({"dimension": dimension, "reducer": reducer})
    return self._append_verb("reduce", **kwargs)

def concept(*reference):
  """Reference to a semantic concept.

  Parameters
  ----------
    *reference : :obj:`str`
      Keys pointing to the ruleset defining this concept in the rules file of
      an ontology.

  Returns
  -------
    :obj:`CubeProxy`
      A textual reference to the concept that can be solved by the query
      processor.

  Examples
  --------
  >>> sq.concept("entity", "water")
  {
    "type": "concept",
    "reference": [
      "entity",
      "water"
    ]
  }

  """
  obj = {"type": "concept", "reference": reference}
  return CubeProxy(obj)

def entity(*reference, property = None):
  """Reference to a semantic concept being an entity.

  Parameters
  ----------
    *reference : :obj:`str`
      Keys pointing to the ruleset defining this concept within the entity
      category in the rules file of an ontology.

  Returns
  -------
    :obj:`CubeProxy`
      A textual reference to the concept that can be solved by the query
      processor.

  Examples
  --------
  >>> sq.entity("water")
  {
    "type": "concept",
    "reference": [
      "entity",
      "water"
    ]
  }

  """
  obj = {"type": "concept", "reference": ("entity",) + reference}
  if property is not None:
    obj["property"] = property
  return CubeProxy(obj)

def event(*reference, property = None):
  """Reference to a semantic concept being an event.

  Parameters
  ----------
    *reference : :obj:`str`
      Keys pointing to the ruleset defining this concept within the event
      category in the rules file of an ontology.

  Returns
  -------
    :obj:`CubeProxy`
      A textual reference to the concept that can be solved by the query
      processor.

  Examples
  --------
  >>> sq.event("flood")
  {
    "type": "concept",
    "reference": [
      "event",
      "flood"
    ]
  }

  """
  obj = {"type": "concept", "reference": ("event",) + reference}
  if property is not None:
    obj["property"] = property
  return CubeProxy(obj)

def resource(*reference):
  """Reference to a factbase resource.

  Parameters
  ----------
    *reference : :obj:`str`
      Keys pointing to the metadata object describing the resource in the
      layout file of a factbase.

  Returns
  -------
    :obj:`CubeProxy`
      A textual reference to the resource that can be solved by the query
      processor.

  Examples
  --------
  >>> sq.resource("appearance", "brightness")
  {
    "type": "resource",
    "reference": [
      "appearance",
      "brightness"
    ]
  }

  """
  obj = {"type": "resource", "reference": reference}
  return CubeProxy(obj)

def appearance(*reference):
  """Reference to a factbase resource describing appearance.

  Parameters
  ----------
    *reference : :obj:`str`
      Keys pointing to the metadata object describing the resource within the
      appearance category in the layout file of a factbase.

  Returns
  -------
    :obj:`CubeProxy`
      A textual reference to the resource that can be solved by the query
      processor.

  Examples
  --------
  >>> sq.appearance("brightness")
  {
    "type": "resource",
    "reference": [
      "appearance",
      "brightness"
    ]
  }

  """
  obj = {"type": "resource", "reference": ("appearance",) + reference}
  return CubeProxy(obj)

def artifacts(*reference):
  """Reference to a factbase resource describing artifacts.

  Parameters
  ----------
    *reference : :obj:`str`
      Keys pointing to the metadata object describing the resource within the
      artifacts category in the layout file of a factbase.

  Returns
  -------
    :obj:`CubeProxy`
      A textual reference to the resource that can be solved by the query
      processor.

  """
  obj = {"type": "resource", "reference": ("artifacts",) + reference}
  return CubeProxy(obj)

def atmosphere(*reference):
  """Reference to a factbase resource describing atmosphere.

  Parameters
  ----------
    *reference : :obj:`str`
      Keys pointing to the metadata object describing the resource within the
      atmosphere category in the layout file of a factbase.

  Returns
  -------
    :obj:`CubeProxy`
      A textual reference to the resource that can be solved by the query
      processor.

  Examples
  --------
  >>> sq.atmosphere("Color type")
  {
    "type": "resource",
    "reference": [
      "atmosphere",
      "Color type"
    ]
  }

  """
  obj = {"type": "resource", "reference": ("atmosphere",) + reference}
  return CubeProxy(obj)

def reflectance(*reference):
  """Reference to a factbase resource describing reflectance.

  Parameters
  ----------
    *reference : :obj:`str`
      Keys pointing to the metadata object describing the resource within the
      reflectance category in the layout file of a factbase.

  Returns
  -------
    :obj:`CubeProxy`
      A textual reference to the resource that can be solved by the query
      processor.

  Examples
  --------
  >>> sq.reflectance("s2_band01")
  {
    "type": "resource",
    "reference": [
      "reflectance",
      "s2_band01"
    ]
  }

  """
  obj = {"type": "resource", "reference": ("reflectance",) + reference}
  return CubeProxy(obj)

def topography(*reference):
  """Reference to a factbase resource describing topography.

  Parameters
  ----------
    *reference : :obj:`str`
      Keys pointing to the metadata object describing the resource within the
      topography category in the layout file of a factbase.

  Returns
  -------
    :obj:`CubeProxy`
      A textual reference to the resource that can be solved by the query
      processor.

  Examples
  --------
  >>> sq.topography("elevation")
  {
    "type": "resource",
    "reference": [
      "topography",
      "elevation"
    ]
  }

  """
  obj = {"type": "resource", "reference": ("topography",) + reference}
  return CubeProxy(obj)

def result(name):
  """Reference to a another result definition.

  Parameters
  ----------
    name : :obj:`str`
      Name of an existing result definition in the query recipe.

  Returns
  -------
    :obj:`CubeProxy`
      A textual reference to the result that can be solved by the query
      processor.

  Examples
  --------
  >>> sq.result("water_count")
  {
    "type": "result",
    "name": "water_count"
  }

  """
  obj = {"type": "result", "name": name}
  return CubeProxy(obj)

def self():
  """Reference to the active evaluation object itself.

  Returns
  -------
    :obj:`CubeProxy`
      A textual reference to the active evaluation object that can be
      solved by the query processor.

  Examples
  --------
  >>> sq.self()
  {
    "type": "self",
  }

  """
  obj = {"type": "self"}
  return CubeProxy(obj)

def collection(*cubes):
  """Reference multiple data cubes at once.

  Parameters
  ----------
    *cubes : :obj:`CubeProxy`
      Elements of the collection.

  Returns
  -------
    :obj:`CubeCollectionProxy`
      A textual reference to the cube collection that can be solved by the
      query processor.

  Examples
  --------
  >>> sq.collection(sq.entity("water"), sq.entity("vegetation"))
  {
    "type": "collection",
    "elements": [
      {
        "type": "concept",
        "reference": [
          "entity",
          "water"
        ]
      },
      {
        "type": "concept",
        "reference": [
          "entity",
          "vegetation"
        ]
      }
    ]
  }

  """
  obj = {"type": "collection", "elements": list(cubes)}
  return CubeCollectionProxy(obj)

def value_label(label):
  """Label of a numeric index.

  Special value representing a label of a numeric index. Can be used to query
  data cubes by character labels rather than numerical indices, which are the
  actual pixel values.

  Parameters
  ----------
    label : :obj:`str`
      The label.

  Returns
  -------
    :obj:`dict`
      JSON-serializable object that contains the value label, and can be
      understood by the query processor as such.

  """
  obj = {"type": "value_label", "label": label}
  return obj

def geometries(value, **kwargs):
  """Spatial geometries.

  Special value representing one or more spatial vector geometries, such as
  points, lines or polygons. Can be used to apply spatial filters to data
  cubes.

  Parameters
  ----------
    value
      One or more spatial features containing the geometries. Should be given
      as an object that can be read by the initializer of
      :obj:`extent.SpatialExtent`. This includes :obj:`geopandas.GeoDataFrame`
      objects.
    **kwargs
      Additional keyword arguments passed on to the initializer of
      :obj:`extent.SpatialExtent`.

  Returns
  -------
    :obj:`dict`
      JSON-serializable object that contains the geometries, and can be
      understood by the query processor as such.

  """
  obj = {"type": "geometry", "value": SpatialExtent(value, **kwargs)}

def time_instant(value, **kwargs):
  """Time instant.

  Special value representing a single timestamp. Can be used to apply temporal
  filters to data cubes.

  Parameters
  ----------
    value
      The time instant as object that can be read by the initializer of
      :obj:`extent.TemporalExtent`. This includes :obj:`pandas.Timestamp`
      objects, as well as text representations of time instants in different
      formats.
    **kwargs
      Additional keyword arguments passed on to the initializer of
      :obj:`extent.TemporalExtent`.

  Returns
  -------
    :obj:`dict`
      JSON-serializable object that contains the time instant, and
      can be understood by the query processor as such.

  """
  obj = {"type": "time_instant", "value": TemporalExtent(value, **kwargs)}
  return obj

def time_interval(*bounds, **kwargs):
  """Time interval.

  Special value representing an interval between two timestamps. Can be used to
  apply temporal filters to data cubes.

  Parameters
  ----------
    *bounds
      Respectively the start and end of the time interval. Should be given as
      objects that can be read by the initializer of :obj:`extent.TemporalExtent`.
      This includes :obj:`pandas.Timestamp` objects, as well as text
      representations of time instants in different formats. The interval is
      assumed to be closed at both sides.
    **kwargs
      Additional keyword arguments passed on to the initializer of
      :obj:`extent.TemporalExtent`.

  Returns
  -------
    :obj:`dict`
      JSON-serializable object that contains the bounds of the time
      interval, and can be understood by the query processor as such.

  """
  obj = {"type": "time_interval", "value": TemporalExtent(*bounds, **kwargs)}
  return obj