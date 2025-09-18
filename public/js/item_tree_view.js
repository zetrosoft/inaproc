// This script will be loaded by item_tree_view.html
// It expects item_groups_data and items_data to be available globally from the HTML context.

$(document).ready(function() {
    render_item_tree();
});

function render_item_tree() {
    const tree_data = [];
    const item_group_map = {};

    // Build a map for quick lookup of item groups
    item_groups_data.forEach(group => {
        item_group_map[group.name] = {
            id: group.name,
            text: group.name,
            parent: group.parent_item_group || '#', // '#' for root nodes
            icon: 'fa fa-folder', // Folder icon for groups
            data: {
                doctype: 'Item Group'
            }
        };
    });

    // Add item groups to the tree data
    for (const group_name in item_group_map) {
        tree_data.push(item_group_map[group_name]);
    }

    // Add items to the tree data
    items_data.forEach(item => {
        tree_data.push({
            id: item.name,
            text: item.item_name,
            parent: item.item_group || '#', // Parent is its item_group, or root if no group
            icon: 'fa fa-file-o', // File icon for items
            data: {
                doctype: 'Item',
                name: item.name
            }
        });
    });

    // Render the tree using a simple nested UL/LI structure
    const build_nested_list = (elements, parent_id = '#') => {
        const ul = $('<ul>');
        elements
            .filter(el => el.parent === parent_id)
            .forEach(el => {
                const li = $('<li>');
                const link = $('<a>').text(el.text);
                if (el.data.doctype === 'Item') {
                    link.attr('href', `/app/item/${el.data.name}`);
                } else {
                    link.attr('href', `/app/item-group/${el.id}`); // Link to Item Group form
                }
                li.append(link);

                const children = elements.filter(child => child.parent === el.id);
                if (children.length > 0) {
                    li.append(build_nested_list(elements, el.id));
                }
                ul.append(li);
            });
        return ul;
    };

    $('#item-tree-container').empty().append(build_nested_list(tree_data));
}