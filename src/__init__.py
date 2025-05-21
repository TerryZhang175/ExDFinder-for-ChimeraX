# Initialize the ChimeraX plugin

from chimerax.core.toolshed import BundleAPI


class _ExDFinderAPI(BundleAPI):

    api_version = 1     # Use API version 1

    # Register the 'ExDFinder' tool
    @staticmethod
    def start_tool(session, bi, ti):
        # Lazy import to load the module only when the tool is used
        from . import residue_tool
        return residue_tool.ExDFinderTool(session, ti.name)

    # Command registration can be added here if needed in the future
    # @staticmethod
    # def register_command(bi, ci, logger):
    #     from . import residue_cmd
    #     residue_cmd.register_command(logger)

    @staticmethod
    def get_class(class_name):
        # Register custom classes so they can be restored in saved sessions
        if class_name == 'ExDFinderTool':
            from . import residue_tool
            return residue_tool.ExDFinderTool
        return None


bundle_api = _ExDFinderAPI() 