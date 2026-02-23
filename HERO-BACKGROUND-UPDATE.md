# Hero Background Image Update ✅

## Changes Made

### Background Image Updated
Changed the hero section background from external URL to local static file.

**Before:**
```css
background: url('https://images.unsplash.com/photo-1520250497591-112f2f40a3f4?...');
```

**After:**
```css
background: url('{% static "accounts/images/hero-bg.jpg.jpeg" %}');
```

## File Location

**Static File Path:**
```
accounts/static/accounts/images/hero-bg.jpg.jpeg
```

**Template Path:**
```
accounts/templates/accounts/landing.html (Line 78)
```

## How It Works

1. The `{% static %}` template tag generates the correct URL for the static file
2. Django's static file system serves the image from the `accounts/static/` directory
3. The gradient overlay is applied on top: `linear-gradient(rgba(26, 86, 219, 0.9), rgba(4, 108, 78, 0.9))`

## Testing

To see the changes:
1. Refresh your browser at http://localhost:8000
2. Clear browser cache if needed (Ctrl+F5)
3. The hero section should now use the local background image

## Benefits

✅ Faster loading (no external API calls)
✅ Works offline
✅ No dependency on external services
✅ Better control over image quality and size
✅ No rate limiting issues

## Note

The actual file is named `hero-bg.jpg.jpeg` (with double extension). If you want to rename it to just `hero-bg.jpg`, you would need to:
1. Rename the file in `accounts/static/accounts/images/`
2. Update the template to use `hero-bg.jpg` instead of `hero-bg.jpg.jpeg`

---

**Status**: ✅ Complete
**File Modified**: `accounts/templates/accounts/landing.html`
**Docker Status**: Running (changes auto-reload in development mode)
