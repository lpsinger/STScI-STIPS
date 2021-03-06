The STIPS PSF Grid
==================
.. note::

    The STIPS PSF Grid creation and configuration process is still in flux. At 
    the moment there is a somewhat confusing conflation of PSF convolution size
    (which should be mostly to do with available memory and computation speed)
    and how many individual PSF interpolations are used from a given grid. In
    the future, these considerations will be split apart, so the documentation
    here is subject to change.

Overview
--------

Starting with STIPS 1.0.8, STIPS supports (and requires) the use of webbpsf PSF 
grids when creating PSFs for convolution. When the STIPS image convolution step
is performed, it will divide up the image into squares (with size set by the
PSF convolution size configuration item), and a PSF will be generated for each
square, with the PSF detector location set to the centre of that square. As a
result, different regions of the detector will have different PSFs applied to
them.

Internal Image Size
-------------------

The size of the STIPS pre-convolution image is set by the size of the detector
and the `detector oversample <../config_file.html#observation-keywords>`_. In
addition, the image is padded by half of the (oversampled) PSF size on each side
in order to include sources that fall off the detector, but whose PSF may land 
on the detector.

.. math::

	Size = Detector\_Pixel\_Size \times Detector\_Oversample + PSF\_Size

PSF Image Size
--------------

The size of the STIPS generated PSF image depends on the `detector oversample
<../config_file.html#observation-keywords>`_, the `maximum convolution size 
<../config_file.html#psf-convolution-configuration>`_, and the maximum unaliased
size of the PSF generated by webbpsf. The PSF size will be set to the minimum of
the three values below:

* Oversampled Detector Size
* Half of the Maximum Convolution Size
* Maximum Unaliased size :math:`Size = \frac{Oversample \times 15 \times PHOTPLAM}{SCALE}` 
  with the pivot wavelength PHOTPLAM in microns, and the scale in 
  arcseconds/pixel.

Dividing PSF convolution
------------------------

When convolving the PSF, STIPS divides the oversampled detector image into boxes
(with all boxes being square except at the right and bottom edges of the 
detector where uneven division may result in rectangular boxes). Each 
convolution box is the size of the `maximum convolution size 
<../config_file.html#psf-convolution-configuration>`_ parameter, and must fit
both the oversampled PSF and some fraction of the internal image (this is why
the PSF is limited to a maximum size of half of the maximum convolution size).

.. math::

	Size = Maximum\_Convolution\_Size - PSF\_Size
	
Note that the convolution operation can be set to run in parallel.

Example
*******

For example, take a Roman F149 observation oversampled by a factor of 8, with a 
maximum convolution size of 8192.

- PSF Size:

  * :math:`Size_1 = Oversampled\_Detector\_Size = 4096 \times 8 = 32768`

  * :math:`Size_2 = 0.5 \times Maximum\_Convolution\_Size = 0.5 \times 8192 = 4096`

  * :math:`Size_3 = \frac{Oversample \times 15 \times PHOTPLAM}{SCALE} = \frac{8 \times 15 \times 1.4635}{0.11} = 1596`

  * :math:`Size = min(Size_1, Size_2, Size_3) = min(32768, 4096, 1596) = 1596`

- Detector Size
  
  .. math::
  
  	Size = Detector\_Pixel\_Size \times Oversample + PSF\_Size = 4096 \times 8 + 1596 = 34364

- Convolution Box Size
  
  .. math::
  	
	Size = Maximum\_Convolution\_Size - PSF\_Size = 8192 - 1596 = 6596

So, the convolution will be a 6x6 grid, with 25 6596x6596 boxes, 5 6596x1384
boxes, 5 1384x6596 boxes, and 1 1384x1384 box. Thus, 36 PSF locations would be
calculated from the grid.
