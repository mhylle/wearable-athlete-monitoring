"""Open Wearables user lifecycle management."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.services.ow_client import OWClient
from app.services.ow_schemas import ConnectionStatus


async def provision_ow_user(
    athlete: User,
    client: OWClient,
    db: AsyncSession,
) -> str:
    """Create an OW user for a local athlete and store the ow_user_id.

    If the athlete already has an ow_user_id, returns it without creating a new one.
    """
    if athlete.ow_user_id:
        return athlete.ow_user_id

    name_parts = athlete.full_name.split(" ", 1)
    first_name = name_parts[0]
    last_name = name_parts[1] if len(name_parts) > 1 else ""

    ow_user = await client.create_user(
        email=athlete.email,
        first_name=first_name,
        last_name=last_name,
    )

    athlete.ow_user_id = ow_user.id
    db.add(athlete)
    await db.commit()

    return ow_user.id


async def get_garmin_connection_status(
    athlete: User,
    client: OWClient,
) -> ConnectionStatus:
    """Check if the athlete has an active Garmin connection in OW."""
    if not athlete.ow_user_id:
        return ConnectionStatus(connected=False)

    connections = await client.get_user_connections(athlete.ow_user_id)
    for conn in connections:
        if conn.provider == "garmin" and conn.status == "active":
            return ConnectionStatus(
                connected=True,
                provider="garmin",
                connection_id=conn.id,
                connected_at=conn.connected_at,
            )

    return ConnectionStatus(connected=False)


async def get_garmin_connect_url(
    athlete: User,
    client: OWClient,
) -> str:
    """Get the OAuth URL for initiating a Garmin connection.

    The athlete must have an ow_user_id provisioned first.
    """
    if not athlete.ow_user_id:
        msg = "Athlete must be provisioned in Open Wearables first"
        raise ValueError(msg)

    return f"{client._client and client._client.base_url or ''}/api/v1/users/{athlete.ow_user_id}/connections/garmin/authorize"
