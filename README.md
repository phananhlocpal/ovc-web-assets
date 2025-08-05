# OVC Web Assets Repository

This repository stores images and static assets for the website [oispvolunteerclub.vercel.app](https://oispvolunteerclub.vercel.app).

## 📁 Directory Structure

```
├── common-assets/    # Common images (backgrounds, titles, icons)
├── logo/             # Organization and partner logos
└── ovc-image/        # Images for pages
    ├── about-us/     # Images for about us page
    ├── activities/   # Images for activities page
    └── move/         # Images for move page
    └── recruitment/  # Images for recruitment page
```

## 🔗 How to Use

To access images from this repository, use jsDelivr CDN with the following syntax:

```
https://cdn.jsdelivr.net/gh/phananhlocpal/ovc-web-assets@master/<path-to-file>
```

### Examples:

- OVC Logo:

  ```
  https://cdn.jsdelivr.net/gh/phananhlocpal/ovc-web-assets@master/logo/ovc.webp
  ```

- Main Background:

  ```
  https://cdn.jsdelivr.net/gh/phananhlocpal/ovc-web-assets@master/common-assets/main-bg.webp
  ```

- Hero Section Image:
  ```
  https://cdn.jsdelivr.net/gh/phananhlocpal/ovc-web-assets@master/ovc-image/about-us/hero/1.webp
  ```

## 📋 Usage Guide

### 1. Adding New Images

1. Clone this repository to your local machine
2. Add image files to the appropriate directory
3. Commit and push to GitHub
4. Use jsDelivr URL to access the images

### 2. Image Optimization

- Use WebP format for optimal file size
- Compress images before uploading
- Use meaningful and descriptive file names

### 3. Using in Code

```html
<!-- HTML -->
<img
  src="https://cdn.jsdelivr.net/gh/phananhlocpal/ovc-web-assets@master/logo/ovc.webp"
  alt="OVC Logo"
/>
```

```css
/* CSS */
.hero-section {
  background-image: url("https://cdn.jsdelivr.net/gh/phananhlocpal/ovc-web-assets@master/common-assets/main-bg.webp");
}
```

```javascript
// JavaScript/React
const logoUrl =
  "https://cdn.jsdelivr.net/gh/phananhlocpal/ovc-web-assets@master/logo/ovc.webp";
```

## ⚠️ Important Notes

- **File Size Limit**: Only upload files under 20MB
- **Recommended Formats**: WebP, PNG, JPG/JPEG
- **File Naming**: Use meaningful names without spaces (use hyphens instead)
- **Updates**: After pushing new code, it may take a few minutes for jsDelivr to update the cache

## 📞 Contact

If you have any issues or need support, please create an issue in this repository or contact me via anhloc280@gmail.com

---

_Repository managed by OISP Volunteer Club_
