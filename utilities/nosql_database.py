from typing import Any, Dict, List, Optional, Union, Iterable, Literal, Sequence

import requests
import json

import pymongo.collection
import bsonjs
import pymongo
import pymongo.errors
import pymongo.response

from pymongo.collection import Collection
from pymongo.database import Database

# from bson.raw_bson import RawBSONDocument


def truncate_word(content: Any, *, length: int, suffix: str = "...") -> str:
    """
    Truncate a string to a certain number of words, based on the max string
    length.
    """

    if not isinstance(content, str) or length <= 0:
        return content

    if len(content) <= length:
        return content

    return content[: length - len(suffix)].rsplit(" ", 1)[0] + suffix


class NoSQLDatabase:
    """pymongo wrapper around a NoSQL database."""

    def __init__(
        self,
        client: pymongo.MongoClient,
        database_name: str,
        ignore_collections: Optional[List[str]] = None,
        include_collections: Optional[List[str]] = None,
        sample_rows_in_collection_info: int = 3,
        indexes_in_collection_info: bool = False,
        custom_collection_info: Optional[dict] = None,
        sample_documents: int = 1,
        max_string_length: int = 30000,
    ):
        """Create pymongo client from MongoDB URI."""
        self._client = client
        self._database: Database = client.get_database(database_name)
        self.dialect: str = "mongodb"  # supports only MongoDB

        if include_collections and ignore_collections:
            raise ValueError(
                "Cannot specify both include_collections and ignore_collections"
            )

        # including view support by adding the views as well as collections to the all
        # collections list if view_support is True
        self._all_collections = set(self.get_collection_names())

        # ignore / include collections
        self._include_collections = (
            set(include_collections) if include_collections else set()
        )
        if self._include_collections:
            missing_collections = self._include_collections - self._all_collections
            if missing_collections:
                raise ValueError(
                    f"include_collections {missing_collections} not found in database"
                )
        self._ignore_collections = (
            set(ignore_collections) if ignore_collections else set()
        )
        if self._ignore_collections:
            missing_collections = self._ignore_collections - self._all_collections
            if missing_collections:
                raise ValueError(
                    f"ignore_collections {missing_collections} not found in database"
                )

        # collections that are usable after ignoring / including
        usable_collections = self.get_usable_collection_names()
        self._usable_collections = (
            set(usable_collections) if usable_collections else self._all_collections
        )

        # set sample rows in collection info
        if not isinstance(sample_rows_in_collection_info, int):
            raise TypeError("sample_rows_in_collection_info must be an integer")

        self._sample_rows_in_collection_info = sample_rows_in_collection_info
        self._indexes_in_collection_info = indexes_in_collection_info

        self._custom_collection_info = custom_collection_info
        if self._custom_collection_info:
            if not isinstance(self._custom_collection_info, dict):
                raise TypeError(
                    "collection_info must be a dictionary with table names as keys and the "
                    "desired table info as values"
                )
            # only keep the tables that are also present in the database
            intersection = set(self._custom_collection_info).intersection(
                self._all_collections
            )
            self._custom_collection_info = dict(
                (table, self._custom_collection_info[table])
                for table in self._custom_collection_info
                if table in intersection
            )

        self._max_string_length = max_string_length
        self.sample_documents = sample_documents

    @classmethod
    def from_uri(cls, uri: str, **kwargs: Any) -> "NoSQLDatabase":
        """Construct a pymongo client from MongoDB URI."""
        # kwargs = {**kwargs, "document_class": RawBSONDocument}
        client = pymongo.MongoClient(uri, **kwargs)
        database_name = client.get_default_database().name
        return cls(client, database_name)

    def get_collection_names(self) -> List[str]:
        """Get names of collections available in the database."""
        return self._database.list_collection_names()

    def get_usable_collection_names(self) -> Iterable[str]:
        """Get names of collections available."""
        if self._include_collections:
            return sorted(self._include_collections)
        return sorted(self._all_collections - self._ignore_collections)

    def get_collection(self, collection_name: str) -> Collection:
        """Get a collection by name."""
        return self._database.get_collection(collection_name)

    def run_command(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Run a MongoDB command."""
        return self._database.command(command)

    @property
    def collection_info(self) -> str:
        """Information about all tables in the database."""
        return self.get_collection_info()

    def get_collection_info(
        self,
        collection_names: Optional[List[str]] = None,
        use_external_uri: Optional[Union[str, bool]] = False,
    ) -> str:
        """
        Get the collections info from the pymongo client and create info locally.
        If `use_external_uri` arg is passed then pass in the schema from an external URI.
        """
        if use_external_uri:
            external_schema_json = self.get_external_mongoose_schema(use_external_uri)
            return self.build_external_schema(external_schema_json)

        db = self._client.get_database()
        all_collection_names = self.get_collection_names()

        if collection_names is not None:
            missing_collections = set(collection_names).difference(all_collection_names)
            if missing_collections:
                raise ValueError(
                    f"Collection names {missing_collections} not found in database"
                )
            collection_names = collection_names
        else:
            collection_names = all_collection_names

        collection_info = []

        for collection_name in collection_names:
            collection = db.get_collection(collection_name)
            collection_info.append(self._get_collection_info(collection))

        return "\n\n".join(collection_info)

    def _get_collection_info(self, collection: pymongo.collection.Collection) -> str:
        info = f"Collection Name: {collection.name}\n"

        # Get indexes
        indexes = collection.index_information()
        if indexes:
            info += "Indexes:\n"
            for index_name, index_info in indexes.items():
                info += f"\tName: {index_name}, Key: {index_info['key']}\n"

        # Get sample documents
        if self.sample_documents > 0:
            sample_document = collection.find_one()
            if sample_document:
                info += f"Sample Document: {bsonjs.dumps(sample_document.raw).replace(' ', '')}"  # .raw comes from RawBSONDocument

        info = self._truncate_string(info)
        return info.strip()

    def build_external_schema(self, schema: Dict[str, Any]) -> str:
        """
        Build collections schema string using the external mongoose schema structure.
        Input:
        {
            "schema": {
                "collection_name": {
                    ...collection schema...
                }
            }
        }
        Output:
        Collection Name: <>
            Schema: {...}
        Collection Name: <>
            Schema: {...}
        ...
        """
        final_info = ""
        for collection_name, collection_schema in schema.items():
            info = f"Collection Name: {collection_name}"
            info += f"\tSchema: {json.dumps(collection_schema).replace(' ', '')}"
            final_info += info

        return final_info

    def _truncate_string(self, content: str) -> str:
        """
        Truncate a string to a certain number of characters, based on the max string
        length.
        """

        if not isinstance(content, str) or self._max_string_length <= 0:
            return content

        if len(content) <= self._max_string_length:
            return content

        return content[: self._max_string_length] + "... (truncated)"

    def get_collection_info_no_throw(
        self, collection_names: Optional[List[str]] = None
    ) -> str:
        """Get information about specified collections.

        Follows best practices as specified in: Rajkumar et al, 2022
        (https://arxiv.org/abs/2204.00498)

        If `sample_rows_in_collection_info`, the specified number of sample rows will be
        appended to each collection description. This can increase performance as
        demonstrated in the paper.
        """
        try:
            return self.get_collection_info(collection_names)
        except ValueError as e:
            """Format the error message"""
            return f"Error: {e}"

    def run(
        self,
        command: Union[str, Dict],
        *,
        fetch: Literal["all", "one"] = "all",
    ) -> Union[str, Sequence[Dict[str, Any]]]:
        """Execute a MongoDB command and return the results."""
        if isinstance(command, str):
            return self._execute_query(command, fetch)
        elif isinstance(command, dict):
            return self._execute_operation(command)
        else:
            raise TypeError("Command must be either a string or a dictionary.")

    def run_no_throw(
        self,
        command: str,
        fetch: Literal["all", "one"] = "all",
        include_columns: bool = False,
        *,
        parameters: Optional[Dict[str, Any]] = None,
        execution_options: Optional[Dict[str, Any]] = None,
    ) -> Union[str, Sequence[Dict[str, Any]]]:
        """Execute a SQL command and return a string representing the results.

        If the statement returns rows, a string of the results is returned.
        If the statement returns no rows, an empty string is returned.

        If the statement throws an error, the error message is returned.
        """
        try:
            return self.run(
                command,
                fetch,
                parameters=parameters,
                execution_options=execution_options,
                include_columns=include_columns,
            )
        except pymongo.errors.PyMongoError as e:
            """Format the error message"""
            return f"Error: {e}"

    def _execute_query(
        self,
        query: str,
        fetch: Literal["all", "one"] = "all",
        filter: Literal["{}"] = "{}",
    ) -> Union[str, Sequence[Dict[str, Any]]]:
        """Execute a MongoDB query and return the results."""
        result = self.run_command(query, filter=json.loads(filter))

        if fetch == "all":
            return list(result)
        elif fetch == "one":
            return [result.next()]
        else:
            raise ValueError("Fetch parameter must be either 'one' or 'all'.")

    def _execute_operation(
        self,
        operation: Dict,
    ) -> str:
        """Execute a MongoDB operation and return the results."""
        collection_name = operation["collection"]
        collection = self._database[collection_name]

        if "action" not in operation:
            raise ValueError("Operation dictionary must contain 'action' key.")
        action = operation["action"]

        if action == "insert_one":
            document = operation["document"]
            result = collection.insert_one(document)
            return f"Inserted document with id: {result.inserted_id}"
        elif action == "insert_many":
            documents = operation["documents"]
            result = collection.insert_many(documents)
            return f"Inserted {len(result.inserted_ids)} documents"
        elif action == "update_one":
            filter_ = operation["filter"]
            update = operation["update"]
            result = collection.update_one(filter_, update)
            return f"Updated {result.modified_count} document(s)"
        elif action == "update_many":
            filter_ = operation["filter"]
            update = operation["update"]
            result = collection.update_many(filter_, update)
            return f"Updated {result.modified_count} document(s)"
        elif action == "delete_one":
            filter_ = operation["filter"]
            result = collection.delete_one(filter_)
            return f"Deleted {result.deleted_count} document(s)"
        elif action == "delete_many":
            filter_ = operation["filter"]
            result = collection.delete_many(filter_)
            return f"Deleted {result.deleted_count} document(s)"
        else:
            raise ValueError(f"Unsupported action: {action}")

    def get_context(self) -> Dict[str, Any]:
        """Return database context that you may want in agent prompt."""
        collection_names = self.get_usable_collection_names()
        collections_info = self.get_collection_info_no_throw()
        return {
            "collections_info": collections_info,
            "collection_names": ", ".join(collection_names),
        }

    def insert_one(
        self, collection_name: str, document: Dict[str, Any]
    ) -> Union[str, None]:
        """Insert a document into a collection."""
        collection = self.get_collection(collection_name)
        try:
            result = collection.insert_one(document)
            return result.inserted_id
        except pymongo.errors.PyMongoError as e:
            return f"Error: {e}"

    def insert_many(
        self, collection_name: str, documents: List[Dict[str, Any]]
    ) -> Union[List[str], None]:
        """Insert multiple documents into a collection."""
        collection = self.get_collection(collection_name)
        try:
            result = collection.insert_many(documents)
            return result.inserted_ids
        except pymongo.errors.PyMongoError as e:
            return [f"Error: {e}" for _ in documents]

    def find(
        self,
        collection_name: str,
        query: Optional[Dict[str, Any]] = None,
        projection: Optional[Dict[str, Any]] = None,
    ) -> Union[List[Dict[str, Any]], str]:
        """Find documents in a collection."""
        collection = self.get_collection(collection_name)
        try:
            cursor = collection.find(query, projection)
            return list(cursor)
        except pymongo.errors.PyMongoError as e:
            return f"Error: {e}"

    def find_one(
        self,
        collection_name: str,
        query: Optional[Dict[str, Any]] = None,
        projection: Optional[Dict[str, Any]] = None,
    ) -> Union[Dict[str, Any], str, None]:
        """Find one document in a collection."""
        collection = self.get_collection(collection_name)
        try:
            result = collection.find_one(query, projection)
            return result
        except pymongo.errors.PyMongoError as e:
            return f"Error: {e}"

    def count_documents(
        self, collection_name: str, query: Optional[Dict[str, Any]] = None
    ) -> Union[int, str]:
        """Count documents in a collection."""
        collection = self.get_collection(collection_name)
        try:
            count = collection.count_documents(query)
            return count
        except pymongo.errors.PyMongoError as e:
            return f"Error: {e}"

    def delete_one(
        self, collection_name: str, query: Dict[str, Any]
    ) -> Union[bool, str]:
        """Delete one document from a collection."""
        collection = self.get_collection(collection_name)
        try:
            result = collection.delete_one(query)
            return result.deleted_count == 1
        except pymongo.errors.PyMongoError as e:
            return f"Error: {e}"

    def delete_many(
        self, collection_name: str, query: Dict[str, Any]
    ) -> Union[int, str]:
        """Delete multiple documents from a collection."""
        collection = self.get_collection(collection_name)
        try:
            result = collection.delete_many(query)
            return result.deleted_count
        except pymongo.errors.PyMongoError as e:
            return f"Error: {e}"

    def update_one(
        self, collection_name: str, query: Dict[str, Any], update: Dict[str, Any]
    ) -> Union[bool, str]:
        """Update one document in a collection."""
        collection = self.get_collection(collection_name)
        try:
            result = collection.update_one(query, {"$set": update})
            return result.modified_count == 1
        except pymongo.errors.PyMongoError as e:
            return f"Error: {e}"

    def update_many(
        self, collection_name: str, query: Dict[str, Any], update: Dict[str, Any]
    ) -> Union[int, str]:
        """Update multiple documents in a collection."""
        collection = self.get_collection(collection_name)
        try:
            result = collection.update_many(query, {"$set": update})
            return result.modified_count
        except pymongo.errors.PyMongoError as e:
            return f"Error: {e}"

    def get_database_info(self) -> Dict[str, Any]:
        """Get information about the database."""
        return self.run_command({"dbStats": 1})

    def get_external_mongoose_schema(self, external_uri: str) -> Dict[str, Any]:
        """
        Get information for the MongoDB collections from outside API with below schema:
        {
            "schema": {
                "collection_name": {
                    ...collection schema...
                }
            }
        }
        """
        response = requests.get(external_uri)
        schema = response.json()
        if "schema" not in schema:
            raise ValueError(
                "External Schema API is not responding with expected repsonse schema"
            )

        return schema["schema"]  # let it throw error so that
