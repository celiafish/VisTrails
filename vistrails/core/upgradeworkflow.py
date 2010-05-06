############################################################################
##
## Copyright (C) 2006-2010 University of Utah. All rights reserved.
##
## This file is part of VisTrails.
##
## This file may be used under the terms of the GNU General Public
## License version 2.0 as published by the Free Software Foundation
## and appearing in the file LICENSE.GPL included in the packaging of
## this file.  Please review the following to ensure GNU General Public
## Licensing requirements will be met:
## http://www.opensource.org/licenses/gpl-license.php
##
## If you are unsure which license is appropriate for your use (for
## instance, you are interested in developing a commercial derivative
## of VisTrails), please contact us at vistrails@sci.utah.edu.
##
## This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
## WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
##
############################################################################

"""This file contains code to handle InvalidPipeline exceptions that contain
upgrade requests."""

from core import debug
import core.db.action
from core.modules.module_registry import get_module_registry, \
     ModuleDescriptor, MissingModule, MissingPort
from core.packagemanager import get_package_manager
from core.vistrail.annotation import Annotation
from core.vistrail.connection import Connection
from core.vistrail.port import Port
from core.vistrail.port_spec import PortSpec
import copy

##############################################################################

class UpgradeWorkflowError(Exception):

    def __init__(self, msg):
        Exception.__init__(self, msg)
        self._msg = msg
        
    def __str__(self):
        return "Upgrading workflow failed.\n" + self._msg

class UpgradeWorkflowHandler(object):

    @staticmethod
    def dispatch_request(controller, module_id, current_pipeline):
        reg = get_module_registry()
        pm = get_package_manager()
        if module_id not in current_pipeline.modules:
            # It is possible that some other upgrade request has
            # already removed the invalid module of this request. In
            # that case, disregard the request.
            print "module %s already handled. skipping" % module_id
            return []
        invalid_module = current_pipeline.modules[module_id]
        pkg = pm.get_package_by_identifier(invalid_module.package)
        if hasattr(pkg.module, 'handle_module_upgrade_request'):
            f = pkg.module.handle_module_upgrade_request
            return f(controller, module_id, current_pipeline)
        else:
            debug.critical('Package cannot handle upgrade request. ' +
                           'VisTrails will attempt automatic upgrade.')
            auto_upgrade = UpgradeWorkflowHandler.attempt_automatic_upgrade
            return auto_upgrade(controller, current_pipeline, module_id)

    @staticmethod
    def check_port_spec(module, port_name, port_type, descriptor=None, 
                        sigstring=None):
        reg = get_module_registry()
        found = False
        try:
            if descriptor is not None:
                s = reg.get_port_spec_from_descriptor(descriptor, port_name,
                                                      port_type)
                found = True
                if s.sigstring != sigstring:
                    msg = ('%s port "%s" of module "%s" exists, but'
                           'signatures differ "%s" != "%s"') % \
                           (port_type.capitalize(), port_name, module.name,
                            s.sigstring, sigstring)
                    raise UpgradeWorkflowError(msg)
        except MissingPort:
            pass

        if not found and \
                not module.has_portSpec_with_name((port_name, port_type)):
            msg = '%s port "%s" of module "%s" does not exist.' % \
                (port_type.capitalize(), port_name, module.name)
            raise UpgradeWorkflowError(msg)

    @staticmethod
    def attempt_automatic_upgrade(controller, pipeline, module_id):
        """attempt_automatic_upgrade(module_id, pipeline): [Action]

        Attempts to automatically upgrade module by simply adding a
        new module with the current package version, and recreating
        all connections and functions. If any of the ports used are
        not available, raise an exception that will trigger the
        failure of the entire upgrade.

        attempt_automatic_upgrade returns a list of actions if
        successful.
        """
        reg = get_module_registry()
        get_descriptor = reg.get_descriptor_by_name
        pm = get_package_manager()
        invalid_module = pipeline.modules[module_id]
        mpkg, mname, mnamespace, mid = (invalid_module.package,
                                        invalid_module.name,
                                        invalid_module.namespace,
                                        invalid_module.id)
        pkg = pm.get_package_by_identifier(mpkg)
        try:
            try:
                d = get_descriptor(mpkg, mname, mnamespace)
            except MissingModule, e:
                r = None
                if pkg.can_handle_missing_modules():
                    r = pkg.handle_missing_module(controller, module_id, 
                                                  pipeline)
                    d = get_descriptor(mpkg, mname, mnamespace)
                if not r:
                    raise e
        except MissingModule, e:
            if mnamespace:
                nss = mnamespace + '|' + mname
            else:
                nss = mname
            msg = ("Could not upgrade module %s from package %s.\n" %
                    (mname, mpkg))
            raise UpgradeWorkflowError(msg)
        assert isinstance(d, ModuleDescriptor)
        
        def check_connection_port(port):
            port_type = PortSpec.port_type_map.inverse[port.type]
            UpgradeWorkflowHandler.check_port_spec(invalid_module,
                                                   port.name, port_type,
                                                   d, port.sigstring)
            
        # check if connections are still valid
        for _, conn_id in pipeline.graph.edges_from(module_id):
            port = pipeline.connections[conn_id].source
            check_connection_port(port)
        for _, conn_id in pipeline.graph.edges_to(module_id):
            port = pipeline.connections[conn_id].destination
            check_connection_port(port)

        # check if function values are still valid
        for function in invalid_module.functions:
            # function_spec = function.get_spec('input')
            UpgradeWorkflowHandler.check_port_spec(invalid_module,
                                                   function.name, 
                                                   'input', d,
                                                   function.sigstring)

        # If we passed all of these checks, then we consider module to
        # be automatically upgradeable. Now create actions that will delete
        # functions, module, and connections, and add new module with corresponding
        # functions and connections.

        return UpgradeWorkflowHandler.replace_module(controller, pipeline, 
                                                     module_id, d)

    @staticmethod
    def replace_generic(controller, pipeline, old_module, new_module,
                        function_remap={}, src_port_remap={}, 
                        dst_port_remap={}, annotation_remap={}):
        ops = []
        ops.extend(controller.delete_module_list_ops(pipeline, [old_module.id]))
        
        for annotation in old_module.annotations:
            if annotation.key not in annotation_remap:
                annotation_key = annotation.key
            else:
                remap = annotation_remap[annotation.key]
                if remap is None:
                    # don't add the annotation back in
                    continue
                elif type(remap) != type(""):
                    ops.extend(remap(annotation))
                    continue
                else:
                    annotation_key = remap

            new_annotation = \
                Annotation(id=controller.id_scope.getNewId(Annotation.vtType),
                           key=annotation_key,
                           value=annotation.value)
            new_module.add_annotation(new_annotation)

        if not old_module.is_group() and not old_module.is_abstraction():
            for port_spec in old_module.port_spec_list:
                if port_spec.type == 'input':
                    if port_spec.name not in dst_port_remap:
                        spec_name = port_spec.name
                    else:
                        remap = dst_port_remap[port_spec.name]
                        if remap is None:
                            continue
                        elif type(remap) != type(""):
                            ops.extend(remap(port_spec))
                            continue
                        else:
                            spec_name = remap
                elif port_spec.type == 'output':
                    if port_spec.name not in src_port_remap:
                        spec_name = port_spec.name
                    else:
                        remap = src_port_remap[port_spec.name]
                        if remap is None:
                            continue
                        elif type(remap) != type(""):
                            ops.extend(remap(port_spec))
                            continue
                        else:
                            spec_name = remap                
                new_spec = port_spec.do_copy(True, controller.id_scope, {})
                new_spec.name = spec_name
                new_module.add_port_spec(new_spec)

        for function in old_module.functions:
            if function.name not in function_remap:
                function_name = function.name
            else:
                remap = function_remap[function.name]
                if remap is None:
                    # don't add the function back in
                    continue                    
                elif type(remap) != type(""):
                    ops.extend(remap(function))
                    continue
                else:
                    function_name = remap

            new_param_vals = [p.strValue for p in function.parameters]
            new_function = controller.create_function(new_module, 
                                                      function_name,
                                                      new_param_vals)
            new_module.add_function(new_function)

        # add the new module
        ops.append(('add', new_module))

        def create_new_connection(src_module, src_port, dst_module, dst_port):
            # spec -> name, type, signature
            output_port_id = controller.id_scope.getNewId(Port.vtType)
            if type(src_port) == type(""):
                output_port_spec = src_module.get_port_spec(src_port, 'output')
                output_port = Port(id=output_port_id,
                                   spec=output_port_spec,
                                   moduleId=src_module.id,
                                   moduleName=src_module.name)
            else:
                output_port = Port(id=output_port_id,
                                   name=src_port.name,
                                   type=src_port.type,
                                   signature=src_port.signature,
                                   moduleId=src_module.id,
                                   moduleName=src_module.name)

            input_port_id = controller.id_scope.getNewId(Port.vtType)
            if type(dst_port) == type(""):
                input_port_spec = dst_module.get_port_spec(dst_port, 'input')
                input_port = Port(id=input_port_id,
                                  spec=input_port_spec,
                                  moduleId=dst_module.id,
                                  moduleName=dst_module.name)
            else:
                input_port = Port(id=input_port_id,
                                  name=dst_port.name,
                                  type=dst_port.type,
                                  signature=dst_port.signature,
                                  moduleId=dst_module.id,
                                  moduleName=dst_module.name)
            conn_id = controller.id_scope.getNewId(Connection.vtType)
            connection = Connection(id=conn_id,
                                    ports=[input_port, output_port])
            return connection

        for _, conn_id in pipeline.graph.edges_from(old_module.id):
            old_conn = pipeline.connections[conn_id]
            if old_conn.source.name not in src_port_remap:
                source_name = old_conn.source.name
            else:
                remap = src_port_remap[old_conn.source.name]
                if remap is None:
                    # don't add this connection back in
                    continue
                elif type(remap) != type(""):
                    ops.extend(remap(old_conn))
                    continue
                else:
                    source_name = remap
                    
            old_dst_module = pipeline.modules[old_conn.destination.moduleId]

            new_conn = create_new_connection(new_module,
                                             source_name,
                                             old_dst_module,
                                             old_conn.destination)
            ops.append(('add', new_conn))
            
        for _, conn_id in pipeline.graph.edges_to(old_module.id):
            old_conn = pipeline.connections[conn_id]
            if old_conn.destination.name not in dst_port_remap:
                destination_name = old_conn.destination.name
            else:
                remap = dst_port_remap[old_conn.destination.name]
                if remap is None:
                    # don't add this connection back in
                    continue
                elif type(remap) != type(""):
                    ops.extend(remap(old_conn))
                    continue
                else:
                    destination_name = remap
                    
            old_src_module = pipeline.modules[old_conn.source.moduleId]
            new_conn = create_new_connection(old_src_module,
                                             old_conn.source,
                                             new_module,
                                             destination_name)
            ops.append(('add', new_conn))
        
        return [core.db.action.create_action(ops)]

    @staticmethod
    def replace_group(controller, pipeline, module_id, new_subpipeline):
        old_group = pipeline.modules[module_id]
        new_group = controller.create_module('edu.utah.sci.vistrails.basic', 
                                             'Group', '', 
                                             old_group.location.x, 
                                             old_group.location.y)
        new_group.pipeline = new_subpipeline
        return UpgradeWorkflowHandler.replace_generic(controller, pipeline, 
                                                      old_group, new_group)
    
    @staticmethod
    def replace_abstraction(controller, pipeline, module_id, new_actions):
        old_abstraction = pipeline.modules[module_id]
        # new_abstraction = controller.
        # FIXME complete this!

    @staticmethod
    def replace_module(controller, pipeline, module_id, new_descriptor,
                       function_remap={}, src_port_remap={}, dst_port_remap={},
                       annotation_remap={}):
        old_module = pipeline.modules[module_id]
        new_module = \
            controller.create_module_from_descriptor(new_descriptor,
                                                     old_module.location.x,
                                                     old_module.location.y)

        return UpgradeWorkflowHandler.replace_generic(controller, pipeline, 
                                                      old_module, new_module,
                                                      function_remap, 
                                                      src_port_remap, 
                                                      dst_port_remap,
                                                      annotation_remap)
