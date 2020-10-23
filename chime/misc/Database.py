import uuid
from typing import List

import google
from google.cloud import firestore
from google.cloud.firestore_v1 import DocumentReference
from wavelink import Track

from chime.util import check_if_playlist_exists


class Database:
    def __init__(self, db):
        self.db = db

    def get_all_playlists(self, user_id: int) -> dict:
        profile_ref: DocumentReference = self.db.collection(str(user_id)).document("profile")
        profile = profile_ref.get()
        profile_data: dict = profile.to_dict()
        if not profile_data:
            raise DatabaseExceptions.NoProfileFoundException()
        if "playlists" not in profile_data.keys():
            raise DatabaseExceptions.ProfileCorruptedException()
        if not len(profile_data["playlists"]) > 0:
            raise DatabaseExceptions.NoPlaylistsException()
        return profile_data["playlists"]

    def create_playlist(self, user_id: int, name: str) -> DocumentReference:
        profile: DocumentReference = self.db.collection(str(user_id)).document("profile")
        if check_if_playlist_exists(profile, name):
            raise DatabaseExceptions.PlaylistAlreadyExistsException()
        playlist_id = str(uuid.uuid4())
        playlist_doc: DocumentReference = self.db.collection(str(user_id)).document(playlist_id)
        playlist_doc.set({"contents": []})
        try:
            profile.update({"playlists": firestore.ArrayUnion([{"name": name, "ref": playlist_id}])})
        except google.api_core.exceptions.NotFound:
            profile.set({"playlists": []}, merge=True)
            profile.update({"playlists": firestore.ArrayUnion([{"name": name, "ref": playlist_id}])})

        return playlist_doc

    def get_playlist_contents(self, user_id: int, name: str) -> dict:
        profile: DocumentReference = self.db.collection(str(user_id)).document("profile")
        playlist_doc: DocumentReference = check_if_playlist_exists(profile, name)
        playlist_data = playlist_doc.get().to_dict()
        if playlist_doc is False:
            raise DatabaseExceptions.PlaylistDoesNotExistException()
        if "contents" not in playlist_data.keys():
            raise DatabaseExceptions.PlaylistCorruptedException(name, user_id)
        return playlist_data["contents"]

    def add_to_playlist(self, user_id: int, name: str, tracks: List[Track]):
        profile: DocumentReference = self.db.collection(str(user_id)).document("profile")
        playlist_doc: DocumentReference = check_if_playlist_exists(profile, name)
        if playlist_doc is False:
            raise DatabaseExceptions.PlaylistDoesNotExistException()
        playlist_doc.update({"contents": firestore.ArrayUnion(
                            [{"title": track_to_add.title, "author": track_to_add.author, "data": track_to_add.id, "url": track_to_add.uri, "id": str(uuid.uuid4()), "duration": track_to_add.duration} for
                             track_to_add in tracks])})



class DatabaseExceptions:
    class NoProfileFoundException(Exception):
        def __init__(self):
            """Gets raised when no profile can be found for the given user id."""
            super(DatabaseExceptions.NoProfile, self).__init__("No profile found for the given user id.")
            self.text = "No profile found for the given user id."

    class ProfileCorruptedException(Exception):
        def __init__(self):
            """Gets raised when the profile of the user seems to be corrupted, i.e. important keys are missing."""
            super(DatabaseExceptions.ProfileCorruptedException, self).__init__("The profile of the given user appears to be corrupted.")
            self.text = "The profile of the given user appears to be corrupted."

    class NoPlaylistsException(Exception):
        def __init__(self):
            """Gets raised the profile of the given user id does not contain any playlists."""
            super(DatabaseExceptions.NoPlaylistsException, self).__init__("The profile of the given user id does not contain any playlists.")
            self.text = "The profile of the given user id does not contain any playlists."

    class PlaylistAlreadyExistsException(Exception):
        def __init__(self):
            """Gets raised when the playlist name meant to be added already exists for the given user id."""
            super(DatabaseExceptions.PlaylistAlreadyExistsException, self).__init__("The playlist name meant to be added already exists for the given user id.")
            self.text = "The playlist name meant to be added already exists for the given user id."

    class PlaylistDoesNotExistException(Exception):
        def __init__(self):
            """Gets raised when the given playlist can't be found."""
            super(DatabaseExceptions.PlaylistDoesNotExistException, self).__init__("The given playlist can't be found.")
            self.text = "The given playlist can't be found."

    class PlaylistCorruptedException(Exception):
        def __init__(self, name: str, user_id: str):
            """Gets raised when the given playlist seems to be corrupted, i.e. important keys are missing."""
            super(DatabaseExceptions.ProfileCorruptedException, self).__init__(f"The given playlist (uid: {user_id}, name: {name}) seems to be corrupted, i.e. important keys are missing.")
            self.text = f"The given playlist (uid: {user_id}, name: {name}) seems to be corrupted, i.e. important keys are missing."


