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

## Dependencies
- pyfdt >= 0.3
- ruamel.yaml >= 0.16.12

# CLI Usage

Point at a binary or directory of binaries. Use the `-v` flag for extra verbose
output indicating things that are possible, but unlikely to be an i.MX boot
image and have been skipped.  The verbose flag will also cause all parsed 
headers to be printed, and the address of any i.MX or FIT file that was 
identified.  By default the tool only prints the file that is being scanned, and 
the name of the results file when the scan is complete.

A summary of the entire parsed image will be captured in a scan results yaml 
file.

```
$ ls -1
emmc_image.bin

$ imx_find_containers emmc_image.bin
Searching emmc_image.bin
Saving scan results: scan_results.2020-09-14T15:43:57-0400.yaml

$ ls -1
emmc_image.bin
scan_results.2020-09-14T15:43:57-0400.yaml
```

## Extracting Images
If the `--extract` flag is set then the contents of any images located in the 
file will be saved as individual files similar to how binwalk operates.  Any 
FIT/FDT/DTB image will also be exported if found, and the FIT source file will 
also be saved.
```
$ ls -1
emmc_image.bin

$ imx_find_containers -e emmc_image.bin
Searching emmc_image.bin
Saving scan results: scan_results.2020-09-14T15:43:57-0400.yaml

$ ls -1
emmc_image.bin
emmc_image.bin--C40C00.dtb
emmc_image.bin--C40C00.dts
emmc_image.bin-2000.bin
emmc_image.bin-C40C00.bin
scan_results.2020-09-14T15:43:57-0400.yaml
```

## Including Images in Scan Results

If the `--include-image-contents` flag is set then the individual images in the 
binary will be included in the scan results yaml file as base64 data.  This does 
increase the amount of time it takes to export the results, but makes it more 
convenient to load the scanned results in python later for further manipulation.
```
$ time imx_find_containers emmc_image.bin > /dev/null
real	0m0.466s
user	0m0.343s
sys	0m0.101s

$ time imx_find_containers -I emmc_image.bin > /dev/null
real	0m25.211s
user	0m24.464s
sys	0m0.357s
```

This option can greatly increase the size of the scan results file as well.
```
$ ls -1
emmc_image.bin

$ imx_find_containers emmc_image.bin
Searching emmc_image.bin
Saving scan results: scan_results.2020-09-14T15:43:57-0400.yaml

$ imx_find_containers -I emmc_image.bin
Searching emmc_image.bin
Saving scan results: scan_results.2020-09-14T15:44:25-0400.yaml

$ ls -sh1 scan_results.*
4.0K scan_results.2020-09-14T15:43:57-0400.yaml
 18M scan_results.2020-09-14T15:44:25-0400.yaml
```

The scan results can be saved as a pickle instead of YAML with the 
`--output-format pickle` command line option.  The pickle results do get written 
faster than the YAML scan results, but result in a less portable binary 
file.
```
$ time imx_find_containers -o pickle emmc_image.bin > /dev/null
real	0m0.444s
user	0m0.310s
sys	0m0.108s
```

However, because the pickle is a binary, scan results that include images are 
smaller than the YAML scan results which include the binaries as base64 strings.
```
real	0m0.486s
user	0m0.340s
sys	0m0.114s
```

# API

## scan_file()
The `imx_find_containers.scan_file()` function can be called programmatically to 
scan a single file for known image types.
```
>>> from imx_find_containers import scan_file
>>> results = scan_file(emmc_image.bin)
```

## find_files()
When called through the command line a directory or multiple files can be 
scanned for image formats.  This can be duplicated using the 
`imx_find_containers.find_files()` function.
```
>>> from imx_find_containers import find_files, scan_file
>>> results = dict(scan_file(f) for f in find_files('./'))
```

## save_results()
Results for multiple files can be saved with the 
`imx_find_containers.save_results()` function.  At the moment this function 
expects the input results to be a dictionary where the keys are the filenames 
that were scanned.
```
>>> from imx_find_containers import find_files, scan_file, save_results
>>> results = dict(scan_file(f) for f in find_files('./'))
>>> save_results(results)
```

Scan results can be saved as pickle by specifying the `output_format` param:
```
>>> from imx_find_containers import find_files, scan_file, save_results
>>> results = dict(scan_file(f) for f in find_files('./'))
>>> save_results(results, output_format='pickle')
```

## open_results()
The yaml (or pickle) scan results are formatted with custom type information, 
this information can be used to re-import the results using the 
`imx_find_containers.open_results()` function.  This is useful for 
programmatically exploring the contents of a scanned image.

```
>>> from imx_find_containers import open_results
>>> results = open_results('scan_results.2020-09-14T15:44:25-0400.yaml')
>>> results.keys()
dict_keys(['emmc_image.bin'])
>>> len(results['emmc_image.bin'])
2
>>> for c in ['emmc_image.bin']: print(c)
0x000000: iMXImageContainer(ContainerHeader(0x0, 0x340, 0x87, 0x2, 0x0, 0x0, 0x2, 0x110))
0x200100: FITContainer(FDTHeader(0xd00dfeed, 0x11422, 0x38, 0x10ae0, 0x28, 0x11, 0x10))
```

The `imx_find_containers.open_results()` function can open both YAML and pickle 
formatted results files.

YAML or pickle files may contain malicious information and the function that 
re-reads the scan results loads type information from the file, only import scan 
results that you trust.
