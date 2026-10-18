# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
lumen-title = Lumen controls
lumen-intro = Make the browser work your way. Start with everyday options below, or open advanced controls when you need them.
lumen-search = Find a setting
lumen-category = Category
lumen-all-categories = All categories
lumen-modified-only = Show changed settings only
lumen-export = Export settings
lumen-import = Import settings
lumen-reset-all = Restore defaults
lumen-reset = Reset
lumen-reset-one = Default restored.
# $name (String) is the setting label.
lumen-reset-setting = Reset
    .aria-label = Reset { $name } to its shipped default
lumen-export-scope = Settings exports contain only the controls on this page. Passwords, cookies, bookmarks, and browsing history are excluded.
lumen-advanced = Advanced controls
lumen-advanced-description = These options can change website behavior. Review their explanations and warnings before making a change.
lumen-advanced-config = Open full advanced configuration
lumen-advanced-config-warning = Additional options in about:config can affect security and compatibility. Keep its warning enabled; this page’s reset and export cover only Lumen controls.
lumen-no-results = No matching settings. Try another phrase or show all categories.
# $count (Number) is the number of matching settings.
lumen-available-count = { $count } matching settings
lumen-saved = Setting saved. Options marked for restart take effect fully after restarting the browser.
# $count (Number) is the number of restored settings.
lumen-reset-complete = Restored { $count } settings. Managed settings were preserved.
lumen-reset-confirm = Restore the settings on this page to their shipped defaults? Other browser settings and personal data will be kept.
lumen-change-confirm = Review this change
# $count (Number) is the number of proposed changes.
# $skipped (Number) is the number of managed or unavailable settings.
lumen-import-confirm = Apply { $count } changes? { $skipped } managed or unavailable settings will be skipped.
# $count (Number) is the number of imported settings.
# $skipped (Number) is the number of managed or unavailable settings.
lumen-import-complete = Imported { $count } settings; skipped { $skipped } managed or unavailable settings.
# $count (Number) is the number of omitted settings.
lumen-export-complete = Settings exported. { $count } unavailable or unsupported custom values were omitted.
lumen-file-too-large = Choose a settings file smaller than 1 MiB.
lumen-custom-value = Custom value — choose a supported option or reset
# $value (String) is the human-readable default choice.
lumen-default-choice = Shipped default: { $value }
# $value (String) is the boolean default, either "true" or "false".
lumen-default-boolean =
    { $value ->
        [true] Shipped default: enabled
       *[false] Shipped default: disabled
    }
lumen-managed = Managed by your organization
lumen-unavailable = Unavailable in this build
# $parent (String) is the parent setting label.
lumen-dependency = Enable “{ $parent }” to adjust this option.
lumen-restart = Restart required for the full effect.
lumen-category-privacy = Privacy
lumen-category-permissions = Site permissions
lumen-category-search = Search and address bar
lumen-category-tabs = Tabs and organization
lumen-category-appearance = Appearance
lumen-category-browsing = Startup and browsing
lumen-category-accessibility = Accessibility and interaction
lumen-category-media = Media and calls
lumen-category-downloads = Downloads
lumen-category-performance = Resource use
lumen-tools-title = More browser tools
lumen-tools-description = Use the browser’s existing tools for tasks that need their own interface.
lumen-tools-nav =
    .aria-label = Browser tools
lumen-tool-general = General settings and import
lumen-tool-privacy = Privacy, permissions, and site data
lumen-tool-passwords = Password manager
lumen-tool-extensions = Extensions and themes
lumen-tool-downloads = Downloads
lumen-tool-keyboard = Keyboard shortcuts
lumen-tool-profiles = Profiles
lumen-tool-troubleshooting = Troubleshooting and recovery
