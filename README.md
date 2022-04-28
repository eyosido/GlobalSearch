# Global Search
Substance 3D Designer plugin extending the search capabilities to multiple packages/folders/graphs/functions at a time using various filters. It is especially useful to locate cooking errors into package functions.

![GlobalSearch_MiniDoc.jpg](https://github.com/eyosido/GlobalSearch/blob/main/doc/GlobalSearch_MiniDoc.jpg)

# Example use cases
- Search for terms in frames or comments, input parameters, variable names, graph names, function names etc.
- Determine which graph parameters have custom functions.
- Find specific variables into functions including package functions, in particular when involved in cooking errors.
- Determine which areas are left to be worked on or temporary and need to be removed before production using TODO and TMP markers.
- Find places where specific variables are being assigned (Set) in functions.

# Features
- Searches text or presets into multiple packages/folders/graphs/functions from a user-defined search root. The list of possible search roots can be refreshed if items have been added/removed in the Explorer view.

- Persistent search filters enabling to search into the following fields:
  . graph name (ID or label)
	. Folder name (ID)
	. Comments and frames
	. Package function names (ID or label)
	. Package function input parameter names (ID)
	. Variables or input parameters in function Get nodes (including Package function)
	. Variables or input parameters in function Set nodes (including Package function)
	
  These search capabilities, in particular the ability to find variable Get/Set usage into package functions are especially useful when developing function code as cooking errors currently do not identify the package function in which an error is present. If the error is related to a variable, the search tool enables to quickly find it.

- Search presets override search filters and search for specific information. The following presets are available:
    . Param functions: searches all graph input parameters to which are assigned custom parameter functions. In a large graph, it is easy to loose track of the input parameters having custom functions, this preset lets you identify them.
	. TODO: searches for TODO strings that can be left in comments to indicate a feature left to implement. This way you can easily manage a TODO list of what's left to do in your graphs.
	. TMP: searches for TMP strings that can be left in comments to indicate a temporary feature that needs to be removed before final release.

- Two search modes: Natural searches for text contained into the items determined by search filters. If not using Natural mode, search is made for exact match, in this case the * wildcard character may be used at the beginning or end of the search text find items by prefix or suffix. Search can be made case sensitive or not.

- Search results presented as hierarchical (Tree) or flat (List) view. In List mode, search results can be sorted by column.

- Persistent Search history keeping the last searches having returned results. Search History can be cleaned in Preferences.

# Requirements
Substance 3D Designer 2019.2 or above.

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
After a package (.sbs) is opened into Designer, the Refresh button (to the right of the Search Into field) must be clicked so the plugin can refresh its list of content to search into.

Use the Search Into field to reduce the search scope to a specific set of components (graphs, package functions etc.).

To perform a search, enter some text in the search field then hit Enter or the Search button (magnifying glass icon). 

The search field is a popup containing a persistent history of searches, which may be used to recall a previous search. This history may be cleared in the plugin's Preferences (cogwheel icon). Special searches neamed TODO and TMP enable user to tag part of their graph with search terms which are then found using a plugin search, this way easing to track the parts of a graphs or function which are either temporary or left to be worked on.

Search results are presented in a Tree view by default, where the result hierarchy may be expanded/collapsed locally. This may be changed to List view by clicking the List icon. The search result view has several columns, you may increase the width of the view if they are not visible by default. Right-clicking on a search result enables to copy into the clipboard various information as well as start a new search from a found result (for example a function name). Search results may be cleared using the Clear button (red X icon). A text at the bottom of the view indicates how many results have been found, or whether no results have been found.

# Package Download
Ready-to-use packages are available in the [releases folder](https://github.com/eyosido/GlobalSearch/tree/main/releases).

# Documentation
Documentation comprises this file as well as content of the [doc folder](https://github.com/eyosido/GlobalSearch/tree/main/doc).

# Known issues / limitations
As of version 1.2.2:
- tree view node expand/collapse in the Search Into combo box/tree may occasionnaly stop working. If this happens, click the Refresh button to the right of the Search Into combo box.
- the outcome of a search cannot be opnened inside a Designer view.
- frame titles are not currently searchable.
- the content of functions attached to FX-Map's internal graph nodes is not searchable.

# Build
To build the .sdplugin file from source, please follow the [procedure](https://substance3d.adobe.com/documentation/sddoc/packaging-plugins-182257149.html) mentioned in the Substance 3D Designer documentation.
