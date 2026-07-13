import re
with open('app/templates/admin.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Add alpine data to body wrapper
content = content.replace('<body class="', '<body x-data="{ activeTab: \'dashboard\' }" class="')

# Update Playlists link
content = content.replace(
    '<a class="flex items-center gap-3 px-3 py-2 text-primary dark:text-primary-fixed-dim font-bold bg-primary-container/10 border-l-2 border-primary transition-all cursor-pointer" hx-get="/admin/" hx-target="body" hx-push-url="true">',
    '<a @click="activeTab = \'dashboard\'" :class="activeTab === \'dashboard\' ? \'text-primary dark:text-primary-fixed-dim font-bold bg-primary-container/10 border-l-2 border-primary\' : \'text-on-surface-variant dark:text-on-surface-variant hover:bg-surface-container-high dark:hover:bg-surface-variant border-l-2 border-transparent\'" class="flex items-center gap-3 px-3 py-2 transition-all cursor-pointer" hx-get="/admin/" hx-target="body" hx-push-url="true">'
)

# Update Providers link
content = content.replace(
    '<a class="flex items-center gap-3 px-3 py-2 text-on-surface-variant dark:text-on-surface-variant hover:bg-surface-container-high dark:hover:bg-surface-variant transition-colors duration-200 cursor-pointer" hx-get="/admin/providers" hx-target="#main-content" hx-swap="outerHTML">',
    '<a @click="activeTab = \'providers\'" :class="activeTab === \'providers\' ? \'text-primary dark:text-primary-fixed-dim font-bold bg-primary-container/10 border-l-2 border-primary\' : \'text-on-surface-variant dark:text-on-surface-variant hover:bg-surface-container-high dark:hover:bg-surface-variant border-l-2 border-transparent\'" class="flex items-center gap-3 px-3 py-2 transition-all cursor-pointer" hx-get="/admin/providers" hx-target="#main-content" hx-swap="outerHTML">'
)

# Update Settings link
content = content.replace(
    '<a class="flex items-center gap-3 px-3 py-2 text-on-surface-variant dark:text-on-surface-variant hover:bg-surface-container-high dark:hover:bg-surface-variant transition-colors duration-200 cursor-pointer" hx-get="/admin/settings" hx-target="#main-content" hx-swap="outerHTML">',
    '<a @click="activeTab = \'settings\'" :class="activeTab === \'settings\' ? \'text-primary dark:text-primary-fixed-dim font-bold bg-primary-container/10 border-l-2 border-primary\' : \'text-on-surface-variant dark:text-on-surface-variant hover:bg-surface-container-high dark:hover:bg-surface-variant border-l-2 border-transparent\'" class="flex items-center gap-3 px-3 py-2 transition-all cursor-pointer" hx-get="/admin/settings" hx-target="#main-content" hx-swap="outerHTML">'
)

# Update Top Nav Analytics
content = content.replace(
    '<a class="text-on-surface-variant dark:text-on-surface-variant hover:text-primary transition-colors cursor-pointer" hx-get="/admin/analytics" hx-target="#main-content" hx-swap="outerHTML">Analytics</a>',
    '<a @click="activeTab = \'analytics\'" :class="activeTab === \'analytics\' ? \'text-primary dark:text-primary-fixed-dim border-b-2 border-primary pb-1\' : \'text-on-surface-variant dark:text-on-surface-variant hover:text-primary transition-colors pb-1\'" class="cursor-pointer" hx-get="/admin/analytics" hx-target="#main-content" hx-swap="outerHTML">Analytics</a>'
)

# Update Top Nav Logs
content = content.replace(
    '<a class="text-on-surface-variant dark:text-on-surface-variant hover:text-primary transition-colors cursor-pointer" hx-get="/admin/logs" hx-target="#main-content" hx-swap="outerHTML">Logs</a>',
    '<a @click="activeTab = \'logs\'" :class="activeTab === \'logs\' ? \'text-primary dark:text-primary-fixed-dim border-b-2 border-primary pb-1\' : \'text-on-surface-variant dark:text-on-surface-variant hover:text-primary transition-colors pb-1\'" class="cursor-pointer" hx-get="/admin/logs" hx-target="#main-content" hx-swap="outerHTML">Logs</a>'
)

# Update Top Nav Dashboard
content = content.replace(
    '<a class="text-primary dark:text-primary-fixed-dim border-b-2 border-primary pb-1 cursor-pointer" hx-get="/admin/" hx-target="body" hx-push-url="true">Dashboard</a>',
    '<a @click="activeTab = \'dashboard\'" :class="activeTab === \'dashboard\' ? \'text-primary dark:text-primary-fixed-dim border-b-2 border-primary pb-1\' : \'text-on-surface-variant dark:text-on-surface-variant hover:text-primary transition-colors pb-1\'" class="cursor-pointer" hx-get="/admin/" hx-target="body" hx-push-url="true">Dashboard</a>'
)

with open('app/templates/admin.html', 'w', encoding='utf-8') as f:
    f.write(content)
print('Done!')
