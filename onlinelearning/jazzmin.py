# Jazzmin Configuration
JAZZMIN_SETTINGS = {
    # title of the window (Will default to current_admin_site.site_title if absent or None)
    "site_title": "Online Learning Platform Admin",

    # Title on the login screen (19 chars max) (defaults to current_admin_site.site_header if absent or None)
    "site_header": "Online Learning",

    # Title on the brand (19 chars max) (defaults to current_admin_site.site_header if absent or None)
    "site_brand": "Online Learning",

    # Logo to use for your site, must be present in static files, used for brand on top left
    "site_logo": None,

    # Logo to use for your site, must be present in static files, used for login form logo (defaults to site_logo)
    "login_logo": None,

    # Logo to use for login form in dark themes (defaults to login_logo)
    "login_logo_dark": None,

    # CSS classes that are applied to the logo above
    "site_logo_classes": "img-circle",

    # Relative path to a favicon for your site, will default to site_logo if absent (ideally 32x32 px)
    "site_icon": None,

    # Welcome text on the login screen
    "welcome_sign": "Welcome to Online Learning Platform",

    # Copyright on the footer
    "copyright": "Online Learning Platform Ltd",

    # List of model admins to search from the search bar, search bar omitted if excluded
    # If you want to use a single search field you dont need to use a list, you can use a simple string 
    "search_model": ["auth.User", "courses.Course", "users.User"],

    # Field name on user model that contains avatar ImageField/URLField/Charfield or a callable that receives the user
    "user_avatar": None,

    ############
    # Top Menu #
    ############
    # Links to put along the top menu
    "topmenu_links": [

        {"name": "Home",  "url": "admin:index", "permissions": ["auth.view_user"]},
        {"name": "Support", "url": "https://github.com/farridav/django-jazzmin/issues", "new_window": True},
        {"model": "auth.User"},
        {"app": "courses"},
        {"app": "users"},
        {"app": "payments"},
        {"app": "certificates"},
        {"app": "discussions"},
        {"app": "live_sessions"},
    ],

    #############
    # Side Menu #
    #############

    # Whether to display the side menu
    "show_sidebar": True,

    # Whether to aut expand the menu
    "navigation_expanded": False,

    # Custom icons for side menu apps/models
    "icons": {
        # App icons
        "auth": "fas fa-users-cog",
        "users": "fas fa-user-graduate",
        "courses": "fas fa-book",
        "payments": "fas fa-credit-card",
        "certificates": "fas fa-certificate",
        "discussions": "fas fa-comments",
        "live_sessions": "fas fa-video",
        "core": "fas fa-home",
        
        # Model icons
        "auth.user": "fas fa-user",
        "auth.Group": "fas fa-users",
        "users.User": "fas fa-user-graduate",
        "users.InstructorApplication": "fas fa-user-tie",
        "courses.Course": "fas fa-book",
        "courses.Module": "fas fa-folder",
        "courses.Lesson": "fas fa-file-alt",
        "courses.Assignment": "fas fa-clipboard-list",
        "courses.Quiz": "fas fa-question-circle",
        "courses.Enrollment": "fas fa-user-plus",
        "courses.AssignmentSubmission": "fas fa-upload",
        "courses.QuizSubmission": "fas fa-edit",
        "payments.Payment": "fas fa-credit-card",
        "certificates.Certificate": "fas fa-certificate",
        "discussions.Discussion": "fas fa-comments",
        "discussions.Comment": "fas fa-comment",
        "live_sessions.LiveSession": "fas fa-video",
    },

    # Custom icons for side menu apps/models when collapsed
    "icons_collapsed": {
        "auth": "fas fa-users-cog",
        "users": "fas fa-user-graduate",
        "courses": "fas fa-book",
        "payments": "fas fa-credit-card",
        "certificates": "fas fa-certificate",
        "discussions": "fas fa-comments",
        "live_sessions": "fas fa-video",
        "core": "fas fa-home",
    },

    # Icons that are used when one is not manually specified
    "default_icon_parents": "fas fa-chevron-circle-right",
    "default_icon_children": "fas fa-circle",

    #################
    # Related Modal #
    #################
    # Use modals instead of popups
    "related_modal_active": True,

    #############
    # UI Tweaks #
    #############
    # Relative paths to custom CSS/JS scripts (must be present in static files)
    "custom_css": None,
    "custom_js": None,
    # Whether to show the UI customizer on the sidebar
    "show_ui_builder": False,

    ###############
    # Change view #
    ###############
    # Render out the change view as a single form, or in tabs, current options are
    # - single
    # - horizontal_tabs (default)
    # - vertical_tabs
    # - collapsible
    # - carousel
    "changeform_format": "horizontal_tabs",
    # changeform_format_overrides = {"auth.user": "collapsible", "auth.group": "vertical_tabs"},
    # Add a language dropdown into the admin
    "language_chooser": False,
}

# Jazzmin UI Customizer
JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": False,
    "brand_small_text": False,
    "brand_colour": "navbar-success",
    "accent": "accent-teal",
    "navbar": "navbar-dark",
    "no_navbar_border": False,
    "navbar_fixed": False,
    "layout_boxed": False,
    "footer_fixed": False,
    "sidebar_fixed": False,
    "sidebar": "sidebar-dark-success",
    "sidebar_nav_small_text": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": False,
    "sidebar_nav_compact_style": False,
    "sidebar_nav_legacy_style": False,
    "sidebar_nav_flat_style": False,
    "theme": "cosmo",
    "dark_mode_theme": None,
    "button_classes": {
        "primary": "btn-primary",
        "secondary": "btn-secondary",
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-success"
    }
}
