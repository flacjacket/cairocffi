# coding: utf8
"""
    cairocffi.ffi_build
    ~~~~~~~~~~~~~~~~~~~

    Build the cffi bindings

    :copyright: Copyright 2013 by Simon Sapin
    :license: BSD, see LICENSE for details.

"""

import os
import subprocess
import sys
from cffi import FFI

# Path hack to import constants when this file is exec'd by setuptools
this_file = os.path.abspath(__file__)
this_dir = os.path.split(this_file)[0]
sys.path.append(this_dir)

import constants


def pkg_config(package, options):
    exe = os.environ.get('PKG_CONFIG', 'pkg-config')
    args = [exe] + options.split() + [package]
    out = subprocess.check_output(args)

    return out.strip().decode()


# TODO: include '-xcb'
SOURCES_CAIRO = '\n'.join(
    '#include <cairo%s.h>' % ext for ext in ['', '-pdf', '-ps', '-svg']
)
try:
    import xcffib
    SOURCES_CAIRO += '\n#include <cairo-xcb.h>\n#include <xcb/xcb.h>'
except ImportError:
    pass

INCLUDES_CAIRO = [inc_dir[2:] for inc_dir in pkg_config('cairo', '--cflags').split() if inc_dir[:2] == '-I']

# Primary cffi definitions
ffi = FFI()

if hasattr(ffi, 'set_source'):
    # PyPy < 2.6 compatibility
    ffi.set_source('cairocffi._ffi', SOURCES_CAIRO, libraries=['cairo'], include_dirs=INCLUDES_CAIRO)

ffi.cdef(constants._CAIRO_HEADERS)

# include xcffib cffi definitions for cairo xcb support
try:
    from xcffib.ffi_build import ffi as xcb_ffi
    ffi.include(xcb_ffi)
    ffi.cdef(constants._CAIRO_XCB_HEADERS)
except ImportError:
    pass

SOURCES_PIXBUF = """
#include <gdk-pixbuf/gdk-pixbuf.h>
"""

INCLUDES_PIXBUF = [inc_dir[2:] for inc_dir in pkg_config('gdk-pixbuf-2.0', '--cflags').split() if inc_dir[:2] == '-I']
LIBS_PIXBUF = [lib[2:] for lib in pkg_config('gdk-pixbuf-2.0', '--libs').split() if lib[:2] == '-l']

# gdk pixbuf cffi definitions
ffi_pixbuf = FFI()
if hasattr(ffi_pixbuf, 'set_source'):
    # PyPy < 2.6 compatibility
    ffi_pixbuf.set_source('cairocffi._ffi_pixbuf', SOURCES_PIXBUF, libraries=LIBS_PIXBUF, include_dirs=INCLUDES_PIXBUF)
ffi_pixbuf.include(ffi)
ffi_pixbuf.cdef('''
    typedef unsigned long   gsize;
    typedef unsigned int    guint32;
    typedef unsigned int    guint;
    typedef unsigned char   guchar;
    typedef char            gchar;
    typedef int             gint;
    typedef gint            gboolean;
    typedef guint32         GQuark;
    typedef void*           gpointer;
    typedef ...             GdkPixbufLoader;
    typedef ...             GdkPixbufFormat;
    typedef ...             GdkPixbuf;
    typedef struct {
        GQuark              domain;
        gint                code;
        gchar              *message;
    } GError;
    typedef enum {
        GDK_COLORSPACE_RGB
    } GdkColorspace;


    GdkPixbufLoader * gdk_pixbuf_loader_new          (void);
    GdkPixbufFormat * gdk_pixbuf_loader_get_format   (GdkPixbufLoader *loader);
    GdkPixbuf *       gdk_pixbuf_loader_get_pixbuf   (GdkPixbufLoader *loader);
    gboolean          gdk_pixbuf_loader_write        (
        GdkPixbufLoader *loader, const guchar *buf, gsize count,
        GError **error);
    gboolean          gdk_pixbuf_loader_close        (
        GdkPixbufLoader *loader, GError **error);

    gchar *           gdk_pixbuf_format_get_name     (GdkPixbufFormat *format);

    GdkColorspace     gdk_pixbuf_get_colorspace      (const GdkPixbuf *pixbuf);
    int               gdk_pixbuf_get_n_channels      (const GdkPixbuf *pixbuf);
    gboolean          gdk_pixbuf_get_has_alpha       (const GdkPixbuf *pixbuf);
    int               gdk_pixbuf_get_bits_per_sample (const GdkPixbuf *pixbuf);
    int               gdk_pixbuf_get_width           (const GdkPixbuf *pixbuf);
    int               gdk_pixbuf_get_height          (const GdkPixbuf *pixbuf);
    int               gdk_pixbuf_get_rowstride       (const GdkPixbuf *pixbuf);
    guchar *          gdk_pixbuf_get_pixels          (const GdkPixbuf *pixbuf);
    gsize             gdk_pixbuf_get_byte_length     (const GdkPixbuf *pixbuf);
    gboolean          gdk_pixbuf_save_to_buffer      (
        GdkPixbuf *pixbuf, gchar **buffer, gsize *buffer_size,
        const char *type, GError **error, ...);

    void              gdk_cairo_set_source_pixbuf    (
        cairo_t *cr, const GdkPixbuf *pixbuf,
        double pixbuf_x, double pixbuf_y);


    void              g_object_ref                   (gpointer object);
    void              g_object_unref                 (gpointer object);
    void              g_error_free                   (GError *error);
    void              g_type_init                    (void);
''')


if __name__ == '__main__':
    ffi.compile()
    ffi_pixbuf.compile()
