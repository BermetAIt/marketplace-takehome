"""Valid listing status transitions (server-side)."""

from fastapi import HTTPException, status

from app.models.listing import Listing, ListingStatus


def assert_owner_can_set_status(listing: Listing, new_status: ListingStatus, is_admin: bool) -> None:
    if is_admin:
        return
    current = listing.status
    allowed = {
        ListingStatus.draft: (
            ListingStatus.draft,
            ListingStatus.pending_review,
            ListingStatus.archived,
        ),
        ListingStatus.pending_review: (
            ListingStatus.pending_review,
            ListingStatus.archived,
            ListingStatus.draft,
        ),
        ListingStatus.approved: (
            ListingStatus.approved,
            ListingStatus.pending_review,
            ListingStatus.archived,
            ListingStatus.inactive,
            ListingStatus.sold,
        ),
        ListingStatus.rejected: (ListingStatus.rejected, ListingStatus.draft, ListingStatus.archived),
        ListingStatus.archived: (ListingStatus.archived, ListingStatus.draft),
        ListingStatus.inactive: (ListingStatus.inactive, ListingStatus.approved, ListingStatus.archived),
        ListingStatus.sold: (ListingStatus.sold, ListingStatus.archived),
    }
    if new_status not in allowed.get(current, ()):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status transition {current.value} -> {new_status.value}",
        )
