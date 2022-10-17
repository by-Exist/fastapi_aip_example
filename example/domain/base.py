from typing import Protocol, Union


class IResource(Protocol):
    """리소스 이름을 관리하기 위해 사용하는 프로토콜입니다."""

    @property
    def identifier(self) -> str:
        """리소스 식별자를 반환합니다.

        Returns:
            str: 일반적으로 리소스 식별자를 반환합니다.
            리소스가 싱글톤일 경우 리소스를 표현하는 단수 명사를 반환합니다.

        Example:
            normal
             = return str(self.id)
            singleton
             = return "config"
        """
        ...

    @classmethod
    @property
    def collection_identifier(cls) -> str | None:
        """컬렉션 식별자를 반환합니다.

        Returns:
            str | None: 일반적으로 리소스를 표현하는 복수 명사를 반환합니다.
            리소스가 싱글톤일 경우 None을 반환합니다.

        Example:
            normal
             = return "publishers"
            singleton
             = return None
        """
        ...

    @property
    def parent(self) -> Union["IResource", None]:
        """리소스의 부모 객체 또는 None을 반환합니다."""
        ...


class IResourceType(Protocol):
    """리소스 타입을 관리하기 위해 사용하는 프로토콜입니다."""

    @classmethod
    @property
    def type(cls) -> str:
        """전역적으로 고유한 리소스의 타입을 표현하는 문자열을 반환합니다.

        Returns:
            str: 리소스의 타입을 표현하는 문자열입니다.
            일반적으로 서비스 이름과 타입으로 구성되어 있습니다.
            (ex, "pubsub.googleapis.com/Topic")

        Example:
            서비스 이름은 일반적으로 클라이언트가 서비스를 호출할 때 사용하는 호스트 이름과
            일치합니다. 타입은 일반적으로 리소스의 타입 이름과 일치합니다.
        """
        ...

    @classmethod
    @property
    def pattern(cls) -> str:
        """리소스 이름의 패턴을 표현하는 문자열을 반환합니다.

        Returns:
            str: 리소스 이름의 패턴을 표현하는 문자열입니다. (ex, "projects/{project}/topics/{topic}")

        주의사항
        - pattern은 리소스의 이름을 표현하는 패턴과 반드시 일치해야 합니다.
        - 중괄호 내에 포함되는 패턴 변수는 snake_case로 작성되어야 합니다.
        - 패턴 변수는 _id 접미사를 사용하지 않아야 합니다.
        """
        ...


def build_resource_name(resource: IResource, service_name: str | None = None) -> str:
    """리소스의 이름을 생성하는 함수입니다.

    Args:
        resource (IResource): 인자로 전달되는 resource는 IResource 프로토콜을 만족시켜야 합니다.
        service_name (str | None, optional): 기본값은 None입니다. 지정되지 않을 경우 상대 리소스 이름을 반환합니다. 지정될 경우 전체 리소스 이름을 반환합니다.

    Returns:
        str: 상대(또는 절대) 리소스 이름입니다.


    Example:
        build_resource_name(book)
         -> "books/book_id"

        build_resource_name(book, "library.exampleapis.com")
         -> "//library.exampleapis.com/books/book_id"
    """

    parent = resource.parent
    collection_id: str | None = resource.collection_identifier
    resource_id: str = resource.identifier

    result: list[str] = []
    if parent:
        result.append(build_resource_name(parent))
    if collection_id:
        result.append(collection_id)
    result.append(resource_id)

    if service_name:
        return f"//{service_name}/{'/'.join(result)}"
    return "/".join(result)
