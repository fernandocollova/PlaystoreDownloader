import asyncio

class MultiDownloader:
    def __init__(self, package_list, downloader):
        self.package_list = package_list
        self.downloader = downloader

    def download(self):
        coros = [self.downloader.download(package) for package in self.package_list]
        loop = asyncio.get_event_loop()
        tasks = asyncio.gather(*coros)
        loop.run_until_complete(tasks)
