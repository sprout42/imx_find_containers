
from .imx import iMXImageContainer
from .fit import FITContainer
from . import utils

def _find_next_unknown_addr(container_list, offset, verbose=False):
    # Ensure that this address does not fall in any of the images belonging to 
    # identified containers, if it does, find the next free address.  This is 
    # unfortunately made complicated because the images for containers may be 
    # interleaved. This means that if the chosen offset is in one container, the 
    # "good" address returned by the "c.find_next_addr()" call may fall inside 
    # a container already passed in the container list.
    #
    # The easiest way to handle this is to recursively call this function until 
    # the offset value does not change.
    initial_offset = offset
    for container in container_list:
        offset = container.find_next_addr(offset)

    if offset == initial_offset:
        # Searching through all of the containers did not identify any overlaps, 
        # this address is good.
        if verbose and offset % 0x1000 == 0:
            print(f'offset: {initial_offset:#x} ({utils.now()})')
        return offset

    else:
        # Searching through all of the containers identified an image that 
        # overlapped with the initial offset, but we don't know if any 
        # containers that were searched before the offset was changed conflict 
        # with the newly identified offset so check the containers for address 
        # overlaps again.
        if verbose:
            print(f'offset: {initial_offset:#x} -> {offset:#x} ({utils.now()})')
        offset = _find_next_unknown_addr(container_list, offset, verbose=verbose)
        if verbose:
            print(f'after: {offset:#x} ({utils.now()})')
        return offset


def _find_container(data, increment=4, verbose=False):
        container_list = []
        offset = 0
        while offset < len(data):
            # TODO: I could probably make the list of containers to look for 
            # automatically populate, but my intention is not to go full binwalk 
            # with this tool.
            if iMXImageContainer.is_container(data=data, offset=offset, verbose=verbose):
                c = iMXImageContainer(data, offset, verbose=verbose)
                offset = c.end
                container_list.append(c)

                # iMX container images may be FIT images, check now
                for img in c.images:
                    if FITContainer.is_container(data=img['data'], offset=0, verbose=verbose):
                        if verbose:
                            print(f'Extracting FIT from image @ {img["offset"]:#x}')
                        fit = FITContainer(data=img['data'], offset=0, verbose=verbose)
                        fit.fix_offset(img['range'].start)

                        # If the fit image uses the entire container image, set 
                        # it's data to None
                        if img['range'].stop == fit.end:
                            img['data'] = None

                        # Add the fit image container to the list
                        container_list.append(fit)

            elif FITContainer.is_container(data, offset):
                c = FITContainer(data, offset, verbose=verbose)
                offset = c.end
                container_list.append(c)

            else:
                # Incrementing by 1 will take longer, but be more thorough, the 
                # is_container() function will ensure that container headers 
                # values are sane.
                #
                # The _find_next_unknown_addr() function does the annoying work 
                # to determine what is the next address that has not been 
                # identified as part of a container or image.
                offset = _find_next_unknown_addr(container_list, offset + increment, verbose=verbose)

                # Round up to ensure that the offset is aligned
                if increment > 1:
                    unaligned = offset % increment
                    if unaligned:
                        offset = offset + (increment - unaligned)

        return container_list


def find(filename, increment=4, verbose=False, **kwargs):
    with open(filename, 'rb') as f:
        data = f.read()
    return _find_container(data, increment, verbose)


__all__ = [
    'find',
]
