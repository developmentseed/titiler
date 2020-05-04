import io
import os
import tarfile

import docker


class TitilerLambdaBuilder:
    def __init__(self):
        current_dir = os.path.dirname(os.path.realpath(__file__))
        self.titiler_lambda_package_filepath = os.path.join(current_dir, 'titiler_lambda.zip')

    @staticmethod
    def _get_container():
        print('Building image and retrieving container')
        client = docker.from_env()
        client.images.build(
            path='./lambda',
            tag='lambda:latest'
        )
        return client.containers.run(
            image='lambda:latest',
            command='/bin/bash',
            detach=True
        )

    def _get_package_file_and_write_locally(self, container):
        print('Extracting function package from container')
        file_stream, _ = container.get_archive('/tmp/package.zip')
        with io.BytesIO() as tar_bytes:
            for b in file_stream:
                tar_bytes.write(b)
            tar_bytes.seek(0)
            tar = tarfile.open(mode='r', fileobj=tar_bytes)
            file = tar.extractfile('package.zip')
            with open(self.titiler_lambda_package_filepath, 'wb') as package_out:
                package_out.write(file.read())

    def get_package_path(self):
        container = self._get_container()
        self._get_package_file_and_write_locally(container)
        return self.titiler_lambda_package_filepath
