# Add Sinan Logo to Navbar - Guide

## Steps to Complete

### 1. Save the Logo Image

Save your Sinan logo image to:
```
accounts/static/accounts/images/sinan-logo.png
```

**Important:** 
- The logo should be in PNG format with transparent background
- Recommended size: 200px width x 60px height (or similar ratio)
- The image will be automatically resized to height: 50px in the navbar

### 2. Navbar Code Updated

The navbar has been updated to use the logo image instead of text:

**Before:**
```html
<a class="navbar-brand" href="{% url 'accounts:home' %}">
    <span class="logo-text">
        <i class="fas fa-plane me-2"></i>Mushqila
    </span>
</a>
```

**After:**
```html
<a class="navbar-brand" href="{% url 'accounts:home' %}">
    <img src="{% static 'accounts/images/sinan-logo.png' %}" alt="Sinan Travel" style="height: 50px; width: auto;">
</a>
```

### 3. Logo Styling

Current styling:
- Height: 50px (fixed)
- Width: auto (maintains aspect ratio)
- Positioned in navbar-brand

You can adjust the height by changing the inline style:
```html
style="height: 50px; width: auto;"
```

### 4. Alternative: If Logo Needs Different Styling

If you want more control over the logo appearance, add CSS:

```css
.navbar-logo {
    height: 50px;
    width: auto;
    max-width: 200px;
    object-fit: contain;
}
```

Then use:
```html
<img src="{% static 'accounts/images/sinan-logo.png' %}" alt="Sinan Travel" class="navbar-logo">
```

## File Modified

**Path:** `accounts/templates/accounts/landing.html`
**Section:** Navbar (Lines ~804-808)

## Testing

After adding the logo image:
1. Restart Docker containers
2. Visit http://localhost:8000
3. The Sinan logo should appear in the navbar

## Troubleshooting

### Logo not showing?
1. Check file path: `accounts/static/accounts/images/sinan-logo.png`
2. Run: `docker-compose exec web python manage.py collectstatic --noinput`
3. Restart Docker containers

### Logo too big/small?
Adjust the height value in the style attribute:
- Smaller: `style="height: 40px; width: auto;"`
- Larger: `style="height: 60px; width: auto;"`

### Logo quality issues?
- Use PNG format with transparent background
- Use high-resolution image (2x size for retina displays)
- Recommended: 400px width x 120px height saved as PNG

---

**Status**: ✅ Code Updated (Logo image needs to be added)
**Next Step**: Save logo image to static folder
**File Path**: `accounts/static/accounts/images/sinan-logo.png`
