import logging
from pathlib import Path
from typing import Iterable

import aiohttp

from .util import Util

logger = logging.getLogger(__name__)

async def aenumerate(asequence, start=0):
    """Asynchronously enumerate an async iterator from a given start value"""
    n = start
    async for elem in asequence:
        yield n, elem
        n += 1


class ApkDownloader:
    def __init__(self, headers, cookies, progress) -> None:
        self.headers = headers
        self.cookies = cookies
        self.progress = progress

    async def _download_single_file(
        self,
        destination_file: Path,
        server_response: aiohttp.ClientResponse,
        show_progress_bar: bool = False,
        download_str: str = "Downloading file",
        error_str: str = "Unable to download the entire file",
    ) -> Iterable[int]:
        """
        Internal method to download a file contained in a server response and save it
        to a specific destination.

        :param destination_file: The destination path where to save the downloaded file.
        :param server_response: The response from the server, containing the content of
                                the file to be saved.
        :param show_progress_bar: Flag indicating whether to show a progress bar in the
                                terminal during the download of the file.
        :param download_str: The message to show next to the progress bar during the
                            download of the file
        :param error_str: The error message of the exception that will be raised if
                        the download of the file fails.
        :return: A generator that returns the download progress (0-100) at each
                iteration.
        """
        chunk_size = 1024
        file_size = int(server_response.headers["Content-Length"])

        # Download the file and save it, yielding the progress (in the range 0-100).
        with open(destination_file, "wb") as f:
            last_progress = 0
            progress = Util.show_list_progress(
                server_response.content.iter_chunked(chunk_size),
                interactive=show_progress_bar,
                unit=" KB",
                total=(file_size // chunk_size),
                description=download_str,
            )
            async for index, chunk in aenumerate(progress):
                current_progress = 100 * index * chunk_size // file_size
                if current_progress > last_progress:
                    last_progress = current_progress
                    yield last_progress
                f.write(chunk)
            yield 100

        # Check if the entire file was downloaded correctly, otherwise raise an
        # exception.
        if file_size != destination_file.stat().st_size:
            logger.error(
                f"Download of '{destination_file}' failed and will be removed"
            )
            try:
                destination_file.unlink()
            except OSError:
                logger.warning(
                    f"The file '{destination_file}' is corrupted and should be "
                    f"removed manually"
                )
            raise RuntimeError(error_str)

    async def download(self, url, path, download_str, error_str):
        async with aiohttp.ClientSession() as session:
            async with session.get(url=url, headers=self.headers, cookies=self.cookies) as response:
                response.raise_for_status()
                gen = self._download_single_file(
                    path,
                    response,
                    self.progress,
                    download_str,
                    error_str,
                )
                async for progress in gen:
                    yield progress
