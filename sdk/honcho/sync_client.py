import uuid
import datetime
from typing import Dict, Optional, List
import httpx
from .schemas import Message, Metamessage, Document

class GetPage:
    """Base class for receiving Paginated API results"""
    def __init__(self, response: Dict) -> None:
        """Constructor for Page with relevant information about the results and pages

        Args:
            response (Dict): Response from API with pagination information
        """
        self.total = response["total"]
        self.page = response["page"]
        self.page_size = response["size"]
        self.pages = response["pages"]
        self.items =[]

    def next(self):
        """Shortcut method to Get the next page of results"""
        pass

class GetSessionPage(GetPage):
    """Paginated Results for Get Session Requests"""

    def __init__(self, client, options: Dict, response: Dict):
        """Constructor for Page Result from Session Get Request
        
        Args:
            client (Client): Honcho Client
            options (Dict): Options for the request used mainly for next() to filter queries. The two parameters available are user_id which is required and location_id which is optional
            response (Dict): Response from API with pagination information
        """
        super().__init__(response)
        self.client = client
        self.user_id = options["user_id"]
        self.location_id = options["location_id"]
        self.items = [
            Session(
                client=client,
                id=session["id"],
                user_id=session["user_id"],
                location_id=session["location_id"],
                is_active=session["is_active"],
                metadata=session["metadata"],
                created_at=session["created_at"],
            )
            for session in response["items"]
        ]
       
    def next(self):
        """Get the next page of results
        Returns:
            GetSessionPage | None: Next Page of Results or None if there are no more sessions to retreive from a query
        """
        if self.page >= self.pages:
            return None
        return self.client.get_sessions(self.user_id, self.location_id, self.page + 1, self.page_size)

class GetMessagePage(GetPage):
    """Paginated Results for Get Session Requests"""

    def __init__(self, session, response: Dict):
        """Constructor for Page Result from Session Get Request
        
        Args:
            session (Session): Session the returned messages are associated with
            response (Dict): Response from API with pagination information
        """
        super().__init__(response)
        self.session = session
        self.items = [
                Message(
                session_id=session.id,
                id=message["id"],
                is_user=message["is_user"],
                content=message["content"],
                created_at=message["created_at"],
            )
            for message in response["items"]
        ]

    def next(self):
        """Get the next page of results
        Returns:
            GetMessagePage | None: Next Page of Results or None if there are no more messages to retreive from a query
        """
        if self.page >= self.pages:
            return None
        return self.session.get_messages((self.page + 1), self.page_size)

class GetMetamessagePage(GetPage):
    
    def __init__(self, session, options: Dict, response: Dict) -> None:
        """Constructor for Page Result from Metamessage Get Request
        
        Args:
            session (Session): Session the returned messages are associated with
            options (Dict): Options for the request used mainly for next() to filter queries. The two parameters available are message_id and metamessage_type which are both required
            response (Dict): Response from API with pagination information
        """
        super().__init__(response)
        self.session = session
        self.message_id = options["message_id"]
        self.metamessage_type = options["metamessage_type"]
        self.items = [
                Metamessage(
                    id=metamessage["id"],
                    message_id=metamessage["message_id"],
                    metamessage_type=metamessage["metamessage_type"],
                    content=metamessage["content"],
                    created_at=metamessage["created_at"],
                    )
                for metamessage in response["items"]
        ]

    def next(self):
        """Get the next page of results
        Returns:
            GetMetamessagePage | None: Next Page of Results or None if there are no more metamessages to retreive from a query
        """
        if self.page >= self.pages:
            return None
        return self.session.get_metamessages(metamessage_type=self.metamessage_type, message=self.message_id, page=(self.page + 1), page_size=self.page_size)

class GetDocumentPage(GetPage):
    """Paginated results for Get Document requests"""
    def __init__(self, collection, response: Dict) -> None:
        """Constructor for Page Result from Document Get Request
        
        Args:
            collection (Collection): Collection the returned documents are associated with
            response (Dict): Response from API with pagination information
        """
        super().__init__(response)
        self.collection = collection
        self.items = [
            Document(
                id=document["id"],
                collection_id=collection.id,
                content=document["content"],
                metadata=document["metadata"],
                created_at=document["created_at"],
                ) 
            for document in response["items"]
        ]

    def next(self):
        """Get the next page of results
        Returns:
            GetSessionPage | None: Next Page of Results or None if there are no more sessions to retreive from a query
        """
        if self.page >= self.pages:
            return None
        return self.collection.get_documents(page=self.page + 1, page_size=self.page_size)

class GetCollectionPage(GetPage):
    """Paginated results for Get Collection requests"""

    def __init__(self, client, options: Dict, response: Dict):
        """Constructor for page result from Get Collection Request
        
        Args:
            client ( Client): Honcho Client
            options (Dict): Options for the request used mainly for next() to filter queries. The only parameter available is user_id which is required
            response (Dict): Response from API with pagination information
        """
        super().__init__(response)
        self.client = client
        self.user_id = options["user_id"]
        self.items = [
            Collection(
                client=client,
                id=collection["id"],
                user_id=collection["user_id"],
                name=collection["name"],
                created_at=collection["created_at"],
            )
            for collection in response["items"]
        ]
       
    def next(self):
        """Get the next page of results
        Returns:
            GetSessionPage | None: Next Page of Results or None if there are no more sessions to retreive from a query
        """
        if self.page >= self.pages:
            return None
        return self.client.get_collections(user_id=self.user_id, page=self.page + 1, page_size=self.page_size)

class Client:
    """Honcho API Client Object"""

    def __init__(self, app_id: str, base_url: str = "https://demo.honcho.dev"):
        """Constructor for Client"""
        self.base_url = base_url  # Base URL for the instance of the Honcho API
        self.app_id = app_id # Representing ID of the client application
        self.client = httpx.Client()

    @property
    def common_prefix(self):
        """Shorcut for common API prefix. made a property to prevent tampering"""
        return f"{self.base_url}/apps/{self.app_id}"

    def get_session(self, user_id: str, session_id: uuid.UUID):
        """Get a specific session for a user by ID

        Args:
            user_id (str): The User ID representing the user, managed by the user
            session_id (uuid.UUID): The ID of the Session to retrieve

        Returns:
            Session: The Session object of the requested Session

        """
        url = f"{self.common_prefix}/users/{user_id}/sessions/{session_id}"
        response = self.client.get(url)
        response.raise_for_status()
        data = response.json()
        return Session(
            client=self,
            id=data["id"],
            user_id=data["user_id"],
            location_id=data["location_id"],
            is_active=data["is_active"],
            metadata=data["metadata"],
            created_at=data["created_at"]
        )

    def get_sessions(self, user_id: str, location_id: Optional[str] = None, page: int = 1, page_size: int = 50):
        """Return sessions associated with a user paginated

        Args:
            user_id (str): The User ID representing the user, managed by the user
            location_id (str, optional): Optional Location ID representing the location of a session
            page (int, optional): The page of results to return
            page_size (int, optional): The number of results to return

        Returns:
            GetSessionPage: Page or results for get_sessions query

        """
        url = f"{self.common_prefix}/users/{user_id}/sessions?page={page}&size={page_size}" + (
            f"&location_id={location_id}" if location_id else ""
        )
        response = self.client.get(url)
        response.raise_for_status()
        data = response.json()
        options = {
                "location_id": location_id,
                "user_id": user_id
                }
        return GetSessionPage(self, options, data)

    def get_sessions_generator(self, user_id: str, location_id: Optional[str] = None):
        """Shortcut Generator for get_sessions. Generator to iterate through all sessions for a user in an app

        Args:
            user_id (str): The User ID representing the user, managed by the user
            location_id (str, optional): Optional Location ID representing the location of a session

        Yields:
            Session: The Session object of the requested Session

        """
        page = 1
        page_size = 50
        get_session_response = self.get_sessions(user_id, location_id, page, page_size)
        while True:
            # get_session_response = self.get_sessions(user_id, location_id, page, page_size)
            for session in get_session_response.items:
                yield session

            new_sessions = get_session_response.next()
            if not new_sessions:
                break
           
            get_session_response = new_sessions

    def create_session(
        self, user_id: str, location_id: str = "default", metadata: Dict = {}
    ):
        """Create a session for a user

        Args:
            user_id (str): The User ID representing the user, managed by the user
            location_id (str, optional): Optional Location ID representing the location of a session
            metadata (Dict, optional): Optional session metadata

        Returns:
            Session: The Session object of the new Session

        """
        data = {"location_id": location_id, "metadata": metadata}
        url = f"{self.common_prefix}/users/{user_id}/sessions"
        response = self.client.post(url, json=data)
        response.raise_for_status()
        data = response.json()
        return Session(
            self,
            id=data["id"],
            user_id=user_id,
            location_id=location_id,
            metadata=metadata,
            is_active=data["is_active"],
            created_at=data["created_at"],
        )

    def create_collection(
        self, user_id, name: str,
    ):
        """Create a collection for a user

        Args:
            user_id (str): The User ID representing the user, managed by the user
            name (str): unique name for the collection for the user

        Returns:
            Collection: The Collection object of the new Collection

        """
        data = {"name": name}
        url = f"{self.common_prefix}/users/{user_id}/collections"
        response = self.client.post(url, json=data)
        response.raise_for_status()
        data = response.json()
        return Collection(
            self,
            id=data["id"],
            user_id=user_id,
            name=name,
            created_at=data["created_at"],
        )

    def get_collection(self, user_id: str, name: str):
        """Get a specific collection for a user by ID

        Args:
            user_id (str): The User ID representing the user, managed by the user
            name (str): The name of the collection to get

        Returns:
            Collection: The Session object of the requested Session

        """
        url = f"{self.common_prefix}/users/{user_id}/collections/name/{name}"
        response = self.client.get(url)
        response.raise_for_status()
        data = response.json()
        return Collection(
            client=self,
            id=data["id"],
            user_id=data["user_id"],
            name=data["name"],
            created_at=data["created_at"]
        )

    def get_collections(self, user_id: str, page: int = 1, page_size: int = 50):
        """Return collections associated with a user paginated

        Args:
            user_id (str): The User ID representing the user
            page (int, optional): The page of results to return
            page_size (int, optional): The number of results to return

        Returns:
            GetCollectionPage: Page or results for get_collections query

        """
        url = f"{self.common_prefix}/users/{user_id}/collections/all?page={page}&size={page_size}"
        response = self.client.get(url)
        response.raise_for_status()
        data = response.json()
        options = {"user_id": user_id}
        return GetCollectionPage(self, options, data)

    def get_collections_generator(self, user_id: str):
        """Shortcut Generator for get_sessions. Generator to iterate through all sessions for a user in an app

        Args:
            user_id (str): The User ID representing the user, managed by the user

        Yields:
            Collection: The Session object of the requested Session

        """
        page = 1
        page_size = 50
        get_collection_response = self.get_collections(user_id, page, page_size)
        while True:
            # get_collection_response = self.get_collections(user_id, location_id, page, page_size)
            for collection in get_collection_response.items:
                yield collection

            new_collections = get_collection_response.next()
            if not new_collections:
                break
           
            get_collection_response = new_collections


class Session:
    """Represents a single session for a user in an app"""

    def __init__(
        self,
        client: Client,
        id: uuid.UUID,
        user_id: str,
        location_id: str,
        metadata: dict,
        is_active: bool,
        created_at
    ):
        """Constructor for Session"""
        self.base_url: str = client.base_url
        self.client: httpx.Client = client.client
        self.app_id: str = client.app_id
        self.id: uuid.UUID = id
        self.user_id: str = user_id
        self.location_id: str = location_id
        self.metadata: dict = metadata
        self._is_active: bool = is_active
        self.created_at: datetime.datetime = created_at

    @property
    def common_prefix(self):
        """Shortcut for common API prefix. made a property to prevent tampering"""
        return f"{self.base_url}/apps/{self.app_id}"

    def __str__(self):
        """String representation of Session"""
        return f"Session(id={self.id}, app_id={self.app_id}, user_id={self.user_id}, location_id={self.location_id}, metadata={self.metadata}, is_active={self.is_active})"

    @property
    def is_active(self):
        """Returns whether the session is active - made property to prevent tampering"""
        return self._is_active

    def create_message(self, is_user: bool, content: str):
        """Adds a message to the session

        Args:
            is_user (bool): Whether the message is from the user
            content (str): The content of the message

        Returns:
            Message: The Message object of the added message

        """
        if not self.is_active:
            raise Exception("Session is inactive")
        data = {"is_user": is_user, "content": content}
        url = f"{self.common_prefix}/users/{self.user_id}/sessions/{self.id}/messages"
        response = self.client.post(url, json=data)
        response.raise_for_status()
        data = response.json()
        return Message(session_id=self.id, id=data["id"], is_user=is_user, content=content, created_at=data["created_at"])

    def get_message(self, message_id: uuid.UUID) -> Message:
        """Get a specific message for a session based on ID

        Args:
            message_id (uuid.UUID): The ID of the Message to retrieve

        Returns:
            Message: The Message object

        """
        url = f"{self.common_prefix}/users/{self.user_id}/sessions/{self.id}/messages/{message_id}"
        response = self.client.get(url)
        response.raise_for_status()
        data = response.json()
        return Message(session_id=self.id, id=data["id"], is_user=data["is_user"], content=data["content"], created_at=data["created_at"])

    def get_messages(self, page: int = 1, page_size: int = 50) -> GetMessagePage:
        """Get all messages for a session

        Args:
            page (int, optional): The page of results to return
            page_size (int, optional): The number of results to return per page

        Returns:
            GetMessagePage: Page of Message objects

        """
        url = f"{self.common_prefix}/users/{self.user_id}/sessions/{self.id}/messages?page={page}&size={page_size}"
        response = self.client.get(url)
        response.raise_for_status()
        data = response.json()
        return GetMessagePage(self, data)
        
    def get_messages_generator(self):
        """Shortcut Generator for get_messages. Generator to iterate through all messages for a session in an app

        Yields:
            Message: The Message object of the next Message

        """
        page = 1
        page_size = 50
        get_messages_page= self.get_messages(page, page_size)
        while True:
            # get_session_response = self.get_sessions(user_id, location_id, page, page_size)
            for message in get_messages_page.items:
                yield message

            new_messages = get_messages_page.next()
            if not new_messages:
                break
           
            get_messages_page = new_messages

    def create_metamessage(self, message: Message, metamessage_type: str, content: str):
        """Adds a metamessage to a session and links it to a specific message

        Args:
            message (Message): A message to associate the metamessage with
            metamessage_type (str): The type of the metamessage arbitrary itentifier
            content (str): The content of the metamessage

        Returns:
            Metamessage: The Metamessage object of the added metamessage

        """
        if not self.is_active:
            raise Exception("Session is inactive")
        data = {"metamessage_type": metamessage_type, "content": content, "message_id": message.id}
        url = f"{self.common_prefix}/users/{self.user_id}/sessions/{self.id}/metamessages"
        response = self.client.post(url, json=data)
        response.raise_for_status()
        data = response.json()
        return Metamessage(id=data["id"], message_id=message.id, metamessage_type=metamessage_type, content=content, created_at=data["created_at"])


    def get_metamessage(self, metamessage_id: uuid.UUID) -> Metamessage:
        """Get a specific metamessage

        Args:
            message_id (uuid.UUID): The ID of the Message to retrieve

        Returns:
            Message: The Message object

        """
        url = f"{self.common_prefix}/users/{self.user_id}/sessions/{self.id}/metamessages/{metamessage_id}"
        response = self.client.get(url)
        response.raise_for_status()
        data = response.json()
        return Metamessage(id=data["id"], message_id=data["message_id"], metamessage_type=data["metamessage_type"], content=data["content"], created_at=data["created_at"])

    def get_metamessages(self, metamessage_type: Optional[str] = None, message: Optional[Message] = None, page: int = 1, page_size: int = 50) -> GetMetamessagePage:
        """Get all messages for a session

        Args:
            user_id (str): The User ID representing the user, managed by the user
            session_id (int): The ID of the Session to retrieve

        Returns:
            list[Dict]: List of Message objects

        """
        url = f"{self.common_prefix}/users/{self.user_id}/sessions/{self.id}/metamessages?page={page}&size={page_size}"
        if metamessage_type:
            url += f"&metamessage_type={metamessage_type}"
        if message:
            url += f"&message_id={message.id}"
        response = self.client.get(url)
        response.raise_for_status()
        data = response.json()
        options = {
                "metamessage_type": metamessage_type,
                "message_id": message.id if message else None
                }
        return GetMetamessagePage(self, options, data)
        
    def get_metamessages_generator(self, metamessage_type: Optional[str] = None, message: Optional[Message] = None):
        """Shortcut Generator for get_metamessages. Generator to iterate through all metamessages for a session in an app

        Args:
            metamessage_type (str, optional): Optional Metamessage type to filter by
            message (Message, optional): Optional Message to filter by

        Yields:
            Metamessage: The next Metamessage object of the requested query

        """
        page = 1
        page_size = 50
        get_metamessages_page = self.get_metamessages(metamessage_type=metamessage_type, message=message, page=page, page_size=page_size)
        while True:
            # get_session_response = self.get_sessions(user_id, location_id, page, page_size)
            for metamessage in get_metamessages_page.items:
                yield metamessage

            new_messages = get_metamessages_page.next()
            if not new_messages:
                break
           
            get_metamessages_page = new_messages

        
    def update(self, metadata: Dict):
        """Update the metadata of a session

        Args:
            metadata (Dict): The Session object containing any new metadata


        Returns:
            boolean: Whether the session was successfully updated
        """
        info = {"metadata": metadata}
        url = f"{self.common_prefix}/users/{self.user_id}/sessions/{self.id}"
        response = self.client.put(url, json=info)
        success = response.status_code < 400
        self.metadata = metadata
        return success

    def close(self):
        """Closes a session by marking it as inactive"""
        url = f"{self.common_prefix}/users/{self.user_id}/sessions/{self.id}"
        response = self.client.delete(url)
        response.raise_for_status()
        self._is_active = False

class Collection:
    """Represents a single collection for a user in an app"""

    def __init__(
        self,
        client: Client,
        id: uuid.UUID,
        user_id: str,
        name: str, 
        created_at: datetime.datetime, 
    ):
        """Constructor for Collection"""
        self.base_url: str = client.base_url
        self.client: httpx.Client = client.client
        self.app_id: str = client.app_id
        self.id: uuid.UUID = id
        self.user_id: str = user_id
        self.name: str = name
        self.created_at: datetime.datetime = created_at

    @property
    def common_prefix(self):
        """Shortcut for common API prefix. made a property to prevent tampering"""
        return f"{self.base_url}/apps/{self.app_id}"

    def __str__(self):
        """String representation of Collection"""
        return f"Collection(id={self.id}, app_id={self.app_id}, user_id={self.user_id}, name={self.name}, created_at={self.created_at})"

    def update(self, name: str):
        """Update the name of the collection

        Args:
            name (str): The new name of the document

        Returns:
            boolean: Whether the session was successfully updated
        """
        info = {"name": name}
        url = f"{self.common_prefix}/users/{self.user_id}/collections/{self.id}"
        response = self.client.put(url, json=info)
        response.raise_for_status()
        success = response.status_code < 400
        self.name = name
        return success

    def delete(self):
        """Delete a collection and all associated documents"""
        url = f"{self.common_prefix}/users/{self.user_id}/collections/{self.id}"
        response = self.client.delete(url)
        response.raise_for_status()

    def create_document(self, content: str, metadata: Dict = {}):
        """Adds a document to the collection

        Args:
            metadata (Dict): The metadata of the document
            content (str): The content of the document

        Returns:
            Document: The Document object of the added document

        """
        data = {"metadata": metadata, "content": content}
        url = f"{self.common_prefix}/users/{self.user_id}/collections/{self.id}/documents"
        response = self.client.post(url, json=data)
        response.raise_for_status()
        data = response.json()
        return Document(
                collection_id=self.id,
                id=data["id"],
                metadata=metadata,
                content=content,
                created_at=data["created_at"]
            )

    def get_document(self, document_id: uuid.UUID) -> Document:
        """Get a specific document for a collection based on ID

        Args:
            document_id (uuid.UUID): The ID of the Document to retrieve

        Returns:
            Document: The Document object

        """
        url = f"{self.common_prefix}/users/{self.user_id}/collections/{self.id}/documents/{document_id}"
        response = self.client.get(url)
        response.raise_for_status()
        data = response.json()
        return Document(
                collection_id=self.id,
                id=data["id"],
                metadata=data["metadata"],
                content=data["content"],
                created_at=data["created_at"]
            )

    def get_documents(self, page: int = 1, page_size: int = 50) -> GetDocumentPage:
        """Get all documents for a collection

        Args:
            page (int, optional): The page of results to return
            page_size (int, optional): The number of results to return per page

        Returns:
            GetDocumentPage: Page of Document objects

        """
        url = f"{self.common_prefix}/users/{self.user_id}/collections/{self.id}/documents?page={page}&size={page_size}"
        response = self.client.get(url)
        response.raise_for_status()
        data = response.json()
        return GetDocumentPage(self, data)
        
    def get_documents_generator(self):
        """Shortcut Generator for get_documents. Generator to iterate through all documents for a collection in an app

        Yields:
            Document: The Document object of the next Document

        """
        page = 1
        page_size = 50
        get_documents_page= self.get_documents(page, page_size)
        while True:
            for document in get_documents_page.items:
                yield document

            new_documents = get_documents_page.next()
            if not new_documents:
                break
           
            get_documents_page = new_documents

    def query(self, query: str, top_k: int = 5) -> List[Document]:
        """query the documents by cosine distance 
        Args:
            query (str): The query to run
            top_k (int, optional): The number of results to return. Defaults to 5.

        Returns:
            List[Document]: The response from the query with matching documents
        """
        url = f"{self.common_prefix}/users/{self.user_id}/collections/{self.id}/query?query={query}&top_k={top_k}"
        response = self.client.get(url)
        response.raise_for_status()
        data = [
           Document(
               collection_id=self.id,
               content=document["content"],
               id=document["id"],
               created_at=document["created_at"],
               metadata=document["metadata"]
           )
           for document in response.json()
        ]
        return data

    def update_document(self, document: Document, metadata: Optional[Dict], content: Optional[str]) -> Document:
        """Update a document in the collection

        Args:
            document (Document): The Document to update
            metadata (Dict): The metadata of the document
            content (str): The content of the document

        Returns:
            Document: The newly updated Document
        """
        if metadata is None and content is None:
            raise ValueError("metadata and content cannot both be None")
        data = {"metadata": metadata, "content": content}
        url = f"{self.common_prefix}/users/{self.user_id}/collections/{self.id}/documents/{document.id}"
        response = self.client.put(url, json=data)
        response.raise_for_status()
        data = response.json()
        return Document(
            data["id"],
            metadata=data["metadata"],
            content=data["content"],
            created_at=data["created_at"],
            collection_id=data["collection_id"],
        )

    def delete_document(self, document: Document) -> bool:
        """Delete a document from the collection

        Args:
            document (Document): The Document to delete

        Returns:
            boolean: Whether the document was successfully deleted
        """
        url = f"{self.common_prefix}/users/{self.user_id}/collections/{self.id}/documents/{document.id}"
        response = self.client.delete(url)
        response.raise_for_status()
        success = response.status_code < 400
        return success
