#!/usr/bin/env python3.4
# coding: latin-1

# (c) Massachusetts Institute of Technology 2015-2018
# (c) Brian Teague 2018-2019
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os

from pyface.qt import QtGui

from traits.api import (Interface, Constant, HasTraits, Instance, Property, 
                        on_trait_change, HTML)
from traitsui.api import Group, Item
from envisage.api import contributes_to
from cytoflowgui.editors import ColorTextEditor
from cytoflowgui.workflow.workflow_item import WorkflowItem

OP_PLUGIN_EXT = 'edu.mit.synbio.cytoflow.op_plugins'


class IOperationPlugin(Interface):
    """
    Attributes
    ----------
    
    id : Constant
        The Envisage ID used to refer to this plugin
        
    operation_id : Constant
        Same as the "id" attribute of the IOperation this plugin wraps.
        
    short_name : Constant
        The operation's "short" name - for menus and toolbar tool tips
    """

    operation_id = Constant("FIXME")
    short_name = Constant("FIXME")

    def get_operation(self):
        """
        Makes an instance of the IWorkflowOperation that this plugin wraps.
        
        Returns
        -------
        :class:`.IWorkflowOperation`
        """
        
    def get_handler(self, model):
        """
        Makes an instance of a Controller for the operation.  
        
        Parameters
        ----------
        model : IWorkflowOperation
            The model that this handler handles.
        
        Returns
        -------
        :class:`traitsui.Controller`
        """

    def get_icon(self):
        """
        Gets the icon for this operation.
        
        Returns
        -------
        :class:`pyface.ImageResource`
            The SVG icon
        """
        
    @contributes_to(OP_PLUGIN_EXT)
    def get_plugin(self):
        """
        Gets the :mod:`envisage` plugin for this operation (usually `self`).
        
        Returns
        -------
        :class:`envisage.Plugin`
            the plugin instance
        """
        
class PluginHelpMixin(HasTraits):
    
    _cached_help = HTML
    
    def get_help(self):
        """
        Gets the HTML help for this module, deriving the filename from
        the class name.
        
        Returns
        -------
        string
            The HTML help, in a single string.
        """
        
        if self._cached_help == "":
            current_dir = os.path.abspath(__file__)
            help_dir = os.path.split(current_dir)[0]
            help_dir = os.path.split(help_dir)[0]
            help_dir = os.path.join(help_dir, "help")
            
            op = self.get_operation()
            help_file = None
            for klass in op.__class__.__mro__:
                mod = klass.__module__
                mod_html = mod + ".html"
                
                h = os.path.join(help_dir, mod_html)
                if os.path.exists(h):
                    help_file = h
                    break
                
            with open(help_file, encoding = 'utf-8') as f:
                self._cached_help = f.read()
                
        return self._cached_help
                        


          
shared_op_traits = Group(Item('context.estimate_warning',
                              label = 'Warning',
                              resizable = True,
                              visible_when = 'context.estimate_warning',
                              editor = ColorTextEditor(foreground_color = "#000000",
                                                       background_color = "#ffff99")),
                         Item('context.estimate_error',
                               label = 'Error',
                               resizable = True,
                               visible_when = 'context.estimate_error',
                               editor = ColorTextEditor(foreground_color = "#000000",
                                                        background_color = "#ff9191")),
                         Item('context.op_warning',
                              label = 'Warning',
                              resizable = True,
                              visible_when = 'context.op_warning',
                              editor = ColorTextEditor(foreground_color = "#000000",
                                                       background_color = "#ffff99")),
                         Item('context.op_error',
                               label = 'Error',
                               resizable = True,
                               visible_when = 'context.op_error',
                               editor = ColorTextEditor(foreground_color = "#000000",
                                                        background_color = "#ff9191")))

        
class OpHandlerMixin(HasTraits):
    """
    Useful bits for operation handlers.
    """
    
    context = Instance(WorkflowItem)
    
    conditions_names = Property(depends_on = "context.conditions")
    previous_conditions_names = Property(depends_on = "context.previous_wi.conditions")
    statistics_names = Property(depends_on = "context.statistics")
    previous_statistics_names = Property(depends_on = "context.previous_wi.statistics")
    
    # the default traits view
    def default_traits_view(self):
        """
        Gets the default :class:`traits.View` for an operation.
        
        Returns
        -------
        traits.View
            The view for an operation.
        """
        
        raise NotImplementedError("Op handlers must override 'default_traits_view")
    
    # MAGIC: gets value for property "conditions_names"
    def _get_conditions_names(self):
        if self.context and self.context.conditions:
            return sorted(list(self.context.conditions.keys()))
        else:
            return []
    
    # MAGIC: gets value for property "previous_conditions_names"
    def _get_previous_conditions_names(self):
        if self.context and self.context.previous_wi and self.context.previous_wi.conditions:
            return sorted(list(self.context.previous_wi.conditions.keys()))
        else:
            return []
        
    # MAGIC: gets value for property "statistics_names"
    def _get_statistics_names(self):
        if self.context and self.context.statistics:
            return sorted(list(self.context.statistics.keys()))
        else:
            return []
        
    # MAGIC: gets value for property "previous_statistics_names"
    def _get_previous_statistics_names(self):
        if self.context and self.context.previous_wi and self.context.previous_wi.statistics:
            return sorted(list(self.context.previous_wi.statistics.keys()))
        else:
            return []
        
    @on_trait_change('context.op_error_trait', 
                     dispatch = 'ui', 
                     post_init = True)
    def _op_trait_error(self):
        
        # check if we're getting called from the local or remote process
        if self.info is None or self.info.ui is None:
            return
        
        for ed in self.info.ui._editors:
            if ed.name == self.context.op_error_trait:
                err_state = True
            else:
                err_state = False

            if not ed.label_control:
                continue
            
            item = ed.label_control
            
            if not err_state and not hasattr(item, '_ok_color'):
                continue
            
            pal = QtGui.QPalette(item.palette())  # @UndefinedVariable
            
            if err_state:
                # TODO - this worked in Qt4 but not in Qt5.  at least on linux,
                # the color isn't changing.  i wonder if it has to do with the
                # fixed theme engine we're using...
                setattr(item, 
                        '_ok_color', 
                        QtGui.QColor(pal.color(item.backgroundRole())))  # @UndefinedVariable
                pal.setColor(item.backgroundRole(), QtGui.QColor(255, 145, 145))  # @UndefinedVariable
                item.setAutoFillBackground(True)
                item.setPalette(pal)
                item.repaint()
            else:
                pal.setColor(item.backgroundRole(), item._ok_color)
                delattr(item, '_ok_color')
                item.setAutoFillBackground(False)
                item.setPalette(pal)
                item.repaint()
