# Drop all
```
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;
```
6713103
# Delete above block
```
delete from event where extrinsic in (select id from extrinsic where block_number >= 1450);
delete from transfer where extrinsic in (select id from extrinsic where block_number >= 1450);
delete from balance where block_number >= 1450;
delete from extrinsic where block_number >= 1450;
delete from block where block_number >= 1450;
```

# Delete between blocks
```
delete from event where extrinsic in (select id from extrinsic where block_number >= 40772 and block_number <= 40786);
delete from transfer where extrinsic in (select id from extrinsic where block_number >= 40772 and block_number <= 40786);
delete from balance where block_number >= 40772 and block_number <= 40786;
delete from extrinsic where block_number >= 40772 and block_number <= 40786;
delete from block where block_number >= 40772 and block_number <= 40786;
```

# update current balance
gets the most recent balance, based on a block_number
and sets the account current balance to it
useful if some data got lost and one has to drop blocks above
a certain block_number
```
with old_balance as (
	select
		id,
		account,
		block_number,
		max(id) over (partition by account) as max_id
	from balance
	where block_number < 6713104
)
update account   
set current_balance = bub.lid
from (select *,b.id as lid,a.id as aid
from account as a
inner join old_balance b
	on b.account = a.id
where b.id=b.max_id
) as bub
where account.id=bub.aid;
```


with old_balance as (
	select
		id,
		account,
		block_number,
		max(id) over (partition by account) as max_id
	from balance
	where block_number >= 1000
)
delete from account
where exists(
select a.id from account a
inner join old_balance b
	on b.account = a.id
where a.current_balance = b.id
	)

/*
update account   
set current_balance = bub.lid
from (select *,b.id as lid,a.id as aid
from account as a
inner join old_balance b
	on b.account = a.id
where b.id=b.max_id
) as bub
where account.id=bub.aid;
*/

# dummy data
do
$$
begin 
for cnt in  1..10 loop
	insert into account("id") values(cnt);
	insert into balance("id","account",block_number) values(cnt, cnt, 100);
	insert into balance("id","account",block_number) values(cnt*500, cnt, 1000);
	insert into balance("id","account",block_number) values(cnt*10000, cnt, 1000);
	update account set current_balance = cnt*10000 where id=cnt;
end loop;
end;
$$



