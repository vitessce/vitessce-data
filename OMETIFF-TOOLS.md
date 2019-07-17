# OME-TIFF Conversion and Viewing Tools

## APEER OME-TIFF Library

- [Installation and release history](https://pypi.org/project/apeer-ometiff-library/)
- Uses [tifffile](https://pypi.org/project/tifffile) to write the image
- Uses [bioformats](https://www.openmicroscopy.org/bio-formats/) module to generate OME-XML
- OME-XML generated is bare-bones, must add TiffData elements for multi-page OME-TIFFs
- Should also adjust filename, date, and channel elements
- Previously used internal tool from Allen Cell Institute, but APEER is for public use and recieves feedback

## FIJI

- [Installation guide](https://imagej.net/Fiji/Downloads)
- Does not require a server to run
- Use bioformats plugin to validate/view OME-XML data (> Plugins > Bio-Formats > Bio-Formats Importer)
- Good validation errors/warnings for incomplete OME-XML
- Drag and drop or importer to view image (for large images, will sample image data for viewing)

## OMERO

- [Installation guide](https://www.openmicroscopy.org/omero/downloads/)
- Requires a server to run, can request access to demo server
- Must import data through the app, cannot import through website
- Validation errors are not descriptive
- Validation is possibly better than FIJI, given this is from the developers of OME-TIFF
- Can view full resolution, colored image, can see composite of channels or toggle single channels on/off
