# Global Search
Substance 3D Designer plugin extending the search capabilities to multiple packages/folders/graphs/functions at a time using various filters. It is especially useful to locate cooking errors into package functions. Compatible with Substance 3D Designer 12.1.1 to 14.x (and potentially above).

![GlobalSearch_MiniDoc.jpg](https://github.com/eyosido/GlobalSearch/blob/main/doc/GlobalSearch_MiniDoc.png)

# Example use cases
- Search for terms in frames or comments, input parameters, variable names, graph names, function names etc.
- Find graph or function nodes by type.
- Determine which graph parameters have parameter functions.
- Find specific variables into functions including package functions, in particular when involved in cooking errors.
- Determine which areas are left to be worked on or temporary and need to be removed before production using TODO and TMP markers.
- Find places where specific variables are being assigned (Set) in functions.

# Features
- Searches text or presets into multiple packages/folders/graphs/functions from a user-defined search root. The list of possible search roots can be refreshed if items have been added/removed in the Explorer view.

- Search associated to persistent filters performed into the following items:
  - graph name (ID or label)
  - Folder name (ID)
  - Comments and frames
  - Package function names (ID or label)
  - Package function input parameter names (ID)
  - Variables or input parameters in function Get nodes (including Package function)
  - Variables or input parameters in function Set nodes (including Package function)
  - Node ID
	
  These search capabilities, in particular the ability to find variable Get/Set usage into package functions are especially useful when developing function code as cooking errors currently do not identify the package function in which an error is present. If the error is related to a variable, the search tool enables to quickly find it.

- Search presets override search filters and search for specific information. The following presets are available:
  - Param functions: searches all graph input parameters to which are assigned custom parameter functions. In a large graph, it is easy to loose track of the input parameters having custom functions, this preset lets you identify them.
  - TODO: searches for TODO strings that can be left in comments to indicate a feature left to implement. This way you can easily manage a TODO list of what's left to do in your graphs.
  - TMP: searches for TMP strings that can be left in comments to indicate a temporary feature that needs to be removed before final release.
- Search is made within words or for exact words (Whole Word option) with optional wildcards.
- Search results presented as hierarchical (Tree) or flat (List) view. In List mode, search results can be sorted by column.
- Search results (graphs, nodes) may be opened into the Graph View using context menu or double-click (Designer 14 and above only, with limitations due to the Designer API).
- In addition to terms, specific nodes may be searched by type, including graph atomic nodes, library nodes and function nodes. Node type filters may also be used to tailor term searching to specific nodes.
- Searches can be made recursively into user graphs and package functions.
- Found graphs, folders and functions may be shown in the Explorer View using the "Show in Explorer" context menu (Designer 14 and above only).
- Persistent Search history keeping the last searches having returned results. Search History can be cleaned in Preferences.
- Navigation previous/next successful searches with arrow buttons.
- Navigtation through search results with optional opening of the results into the Graph View.
- Search results may be saved into a JSON file.

# Requirements
Substance 3D Designer 12.1.1 to 14.x (and potentially above).

# Installation
- In Substance 3D Designer, open the Plugin Manager (“Tools / Plugin Manager...” menu)
- Click the "INSTALL..." button and select the .sdplugin file.

The plugin will be installed on your user space (on Windows this is (user home)\Documents\Adobe\Adobe Substance 3D Designer\python\sduserplugins) and enabled in the Plugin Manager. You may disable/enable it in the Plugin Manager at any time.

The plugin view is a dock widget integrated in the Designer User Interface. You can resize it, dock it, make it a separate windows just like any other Designer view. If the plugin view is closed it can be restored using the Windows menu.

# Upgrade
If upgrading from a previous version of the plugin, the latter must first be deleted from the user space, on Windows this is:

    <user home>\Documents\Adobe\Adobe Substance 3D Designer\python\sduserplugins
Then, launch Substance 3D Designer to install the new version of the plugin as mentioned above.

# Usage
Use the Search Into field to reduce the search scope to a specific set of components (graphs, package functions etc.).

To perform a search, enter some text in the search field then hit Enter or the Search button (magnifying glass icon). 

The search field is a popup containing a persistent history of searches, which may be used to recall a previous search. This history may be cleared in the plugin's Preferences (cogwheel icon). Special searches neamed TODO and TMP enable user to tag part of their graph with search terms which are then found using a plugin search, this way easing to track the parts of a graphs or function which are either temporary or left to be worked on.

Search results are presented in a Tree view by default, where the result hierarchy may be expanded/collapsed locally. This may be changed to List view by clicking the List icon. The search result view has several columns, you may increase the width of the view if they are not visible by default. Right-clicking on a search result enables to copy into the clipboard various information as well as start a new search from a found result (for example a function name). Search results may be cleared using the Clear button (red X icon). A text at the bottom of the view indicates how many results have been found, or whether no results have been found.

# Package Download
Ready-to-use packages are available in the [Releases section](https://github.com/eyosido/GlobalSearch/releases).

# Documentation
Documentation comprises this file as well as content of the [doc folder](https://github.com/eyosido/GlobalSearch/tree/main/doc).

# Known issues / limitations
As of latest release:
- Supports only Substance Graphs (texturing graphs).
- When unloading the plugin, the Windows menu still contains the mention of the GlobalSearch window even though it does not exist anymore. When re-enabling the plugin after disabling it, its window does not appear automatically, use the Windows/GlobalSearch menu to show it.
- Items withing FX-Map, Pixel Processor or Value Processor graphs cannot currently be opened from the Search Result tree (Designer API limitation in 14.1.1).
- The "Search Into" field is not updated when a graph/package is created/loaded/removed due to the lack of notification from the Designer API (in Designer 14.1.1). The Refresh button updates this field.

# Build
To build the .sdplugin file from source, please follow the [procedure](https://substance3d.adobe.com/documentation/sddoc/packaging-plugins-182257149.html) mentioned in the Substance 3D Designer documentation.

# Support
For support you may join the [Eyosido Soft. Discord server](https://discord.gg/BpUgtTRUdT).
