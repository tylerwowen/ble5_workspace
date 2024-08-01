import abc


class BaseLayout(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def render(self):
        pass
