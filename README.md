# Summary

The `imx_find_containers` tool helps to find i.MX containers in a binary, parses 
the header for the container which indicates (among other things) if the image is
signed, and which processor core the image will be executed on.

Adapted from info in the following NXP docs:
    - IMX8DQXPRM.pdf
    - AN12056.pdf

And the following tools:
    - https://source.codeaurora.org/external/imx/uboot-imx
    - https://source.codeaurora.org/external/imx/imx-mkimage/
    - https://www.nxp.com/webapp/Download?colCode=IMX_CST_TOOL_NEW&location=null

As much as I like writing tools to parse things, the
https://github.com/superna9999/pyfdt/ python module is used to process FIT/FDT
images because it is already written, works, and FIT/FDT parsing is a large set 
of functionality to re-write myself for fun.

# Usage

Simply point at a binary to have it parsed. Use the `-v` flag for extra verbose
output indicating things that are possible, but unlikely to be an i.MX boot
image and have been skipped.

A summary of the entire parsed image will be captured in a yaml file, any
individual images in the binary are extracted as separate files as well to allow
for further processing/analysis. Any FIT/FDT images identified will be exported 
as both blob (dtb) and source (dts) files.

```
$ ls -1
emmc_image.bin

$ imx_find_containers emmc_image.bin
Searching emmc_image.bin
0: ContainerHeader(version=0, length=832, tag=135, flags=2, sw_ver=0, fuse_ver=0, num_images=2, sig_offset=272)
0: FDTHeader(magic=3490578157, totalsize=70690, off_dt_struct=56, off_dt_strings=68320, off_mem_rsvmap=40, version=17, last_comp_version=16)

$ ls -1
emmc_image.bin
emmc_image.bin--C40C00.dtb
emmc_image.bin--C40C00.dts
emmc_image.bin-2000.bin
emmc_image.bin-C40C00.bin
scan_results.2020-09-14T15:43:57-0400.yaml
```
